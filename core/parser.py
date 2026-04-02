"""
parser.py — Robust BibTeX parsing with two-pass fallback strategy.

Pass 1: bibtexparser (fast, clean, handles most well-formed files)
Pass 2: regex-based recovery for entries bibtexparser dropped
"""
from __future__ import annotations

import re
import logging
from collections import Counter
from typing import Optional

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from .models import BibEntry, ParseResult

log = logging.getLogger(__name__)

# Entry types considered "article-like" for filtering
ARTICLE_LIKE_TYPES = {"article", "inproceedings", "conference", "proceedings"}

# Entry types included in "articles + conference" filter
SCHOLARLY_TYPES = ARTICLE_LIKE_TYPES | {"incollection", "phdthesis", "mastersthesis", "techreport"}


def _clean(text: str) -> str:
    """Strip BibTeX braces and normalise whitespace."""
    if not text:
        return ""
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_authors(raw: str) -> list[str]:
    """Split 'Last, First AND Last2, First2' into a list of formatted names."""
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"\band\b", raw, flags=re.IGNORECASE)]
    result = []
    for p in parts:
        if not p:
            continue
        if "," in p:
            last, rest = p.split(",", 1)
            initials = "".join(
                w[0].upper() + "."
                for w in rest.split()
                if w and not w.startswith("{")
            )
            name = f"{last.strip()}"
            if initials:
                name += f" {initials}"
            result.append(name)
        else:
            result.append(p)
    return result


def _normalise_entry(raw: dict) -> BibEntry:
    """Convert a bibtexparser dict into a BibEntry."""
    e = BibEntry()
    e.raw_id     = raw.get("ID", "")
    e.entry_type = raw.get("ENTRYTYPE", "article").lower().strip()

    e.title     = _clean(raw.get("title", ""))
    e.year      = _clean(raw.get("year", ""))
    e.journal   = _clean(raw.get("journal", ""))
    e.booktitle = _clean(raw.get("booktitle", ""))
    e.publisher = _clean(raw.get("publisher", ""))
    e.volume    = _clean(raw.get("volume", ""))
    e.number    = _clean(raw.get("number", raw.get("issue", "")))
    e.issue     = _clean(raw.get("issue", ""))
    e.pages     = _clean(raw.get("pages", ""))
    e.doi       = _clean(raw.get("doi", ""))
    e.url       = _clean(raw.get("url", ""))
    e.abstract  = _clean(raw.get("abstract", ""))

    raw_authors = raw.get("author", raw.get("authors", ""))
    e.authors   = _split_authors(_clean(raw_authors))

    e.has_abstract = bool(e.abstract)

    if not e.title:
        e.malformed = True
        e.malform_reason = "Missing title"

    return e


def _regex_recover(block: str) -> Optional[BibEntry]:
    """
    Very permissive single-entry extractor.
    Handles braces-in-values and multi-line fields.
    """
    header = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", block)
    if not header:
        return None

    entry_type = header.group(1).lower()
    entry_id   = header.group(2).strip()

    fields: dict = {"ENTRYTYPE": entry_type, "ID": entry_id}

    # Match key = {value} patterns (greedy for nested braces)
    for m in re.finditer(
        r"\b(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}",
        block,
        re.DOTALL,
    ):
        key = m.group(1).lower().strip()
        val = m.group(2).strip()
        fields[key] = val

    # Also catch key = "value" patterns
    for m in re.finditer(r'\b(\w+)\s*=\s*"([^"]*)"', block):
        key = m.group(1).lower().strip()
        if key not in fields:
            fields[key] = m.group(2).strip()

    return _normalise_entry(fields)


def parse_bib_content(content: str) -> ParseResult:
    """
    Parse BibTeX string content and return a ParseResult.

    Strategy:
      1. Use bibtexparser for maximum quality on well-formed entries.
      2. Regex-scan raw blocks for entries bibtexparser missed.
      3. Detect duplicate titles.
    """
    result = ParseResult()

    # ── Count raw entry markers ───────────────────────────────────────────────
    raw_ids: set[str] = set()
    raw_blocks: list[str] = []
    for m in re.finditer(r"(@\w+\s*\{[^@]*)", content, re.DOTALL):
        raw_blocks.append(m.group(1).strip())

    result.total_raw = len(raw_blocks)

    # ── Pass 1: bibtexparser ──────────────────────────────────────────────────
    try:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        parser.ignore_nonstandard_types = False
        db = bibtexparser.loads(content, parser=parser)

        for raw in db.entries:
            entry = _normalise_entry(raw)
            result.entries.append(entry)
            raw_ids.add(raw.get("ID", ""))
            if entry.malformed:
                result.malformed_count += 1

    except Exception as exc:
        result.parse_errors.append(f"bibtexparser error: {exc}")
        log.warning("bibtexparser failed: %s", exc)

    # ── Pass 2: regex fallback for missed entries ─────────────────────────────
    recovered = 0
    for block in raw_blocks:
        hdr = re.match(r"@\w+\s*\{\s*([^,\s]+)", block)
        if not hdr:
            continue
        eid = hdr.group(1).strip()
        if eid in raw_ids:
            continue
        recovered_entry = _regex_recover(block)
        if recovered_entry:
            result.entries.append(recovered_entry)
            raw_ids.add(eid)
            recovered += 1
            if recovered_entry.malformed:
                result.malformed_count += 1

    if recovered:
        log.info("Regex fallback recovered %d additional entries", recovered)

    # ── Duplicate title detection ─────────────────────────────────────────────
    title_counts = Counter(
        e.title.lower()
        for e in result.entries
        if e.title
    )
    result.duplicate_titles = [
        t for t, cnt in title_counts.items() if cnt > 1
    ]

    return result


def filter_entries(result: ParseResult, filter_mode: str) -> list[BibEntry]:
    """Apply filter mode to the parsed entries."""
    usable = result.usable

    if filter_mode == "articles_conf":
        return [e for e in usable if e.entry_type in SCHOLARLY_TYPES]
    elif filter_mode == "with_abstract":
        return [e for e in usable if e.has_abstract]
    else:
        return usable


def sort_entries(entries: list[BibEntry], sort_mode: str) -> list[BibEntry]:
    """Sort entries according to user selection."""
    if sort_mode == "alpha_title":
        return sorted(entries, key=lambda e: e.title.lower())
    elif sort_mode == "year_asc":
        return sorted(entries, key=lambda e: (e.year or "0000", e.title.lower()))
    elif sort_mode == "year_desc":
        return sorted(entries, key=lambda e: (e.year or "0000", e.title.lower()), reverse=True)
    else:  # original
        return entries
