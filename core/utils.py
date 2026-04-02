"""
utils.py — Shared utilities for the BibTeX → DOCX app.
"""
from __future__ import annotations

import time
from typing import Iterator

from .models import BibEntry


def estimate_generation_time(entry_count: int) -> str:
    """Rough estimate of document generation time based on entry count."""
    seconds = max(2, entry_count * 0.035)
    if seconds < 60:
        return f"~{int(seconds)}s"
    minutes = seconds / 60
    return f"~{minutes:.1f} min"


def entries_to_preview_rows(entries: list[BibEntry], limit: int = 25) -> list[dict]:
    """Convert entries to a list of dicts suitable for pd.DataFrame display."""
    rows = []
    for e in entries[:limit]:
        rows.append({
            "Title":    (e.title[:90] + "…") if len(e.title) > 90 else e.title,
            "Year":     e.year or "—",
            "Type":     e.entry_type,
            "Authors":  f"{len(e.authors)} author{'s' if len(e.authors) != 1 else ''}",
            "Abstract": "✓" if e.has_abstract else "✗",
        })
    return rows


def safe_filename(name: str) -> str:
    """Sanitise a string for use as a filename (no extension)."""
    import re
    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name or "bibliography_compendium"


def chunked(lst: list, size: int) -> Iterator[list]:
    """Yield successive chunks of `size` from `lst`."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]
