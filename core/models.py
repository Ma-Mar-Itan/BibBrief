"""
models.py — Core data structures for the BibTeX → DOCX pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BibEntry:
    """Normalised representation of a single BibTeX entry."""

    # Internal
    raw_id: str = ""
    entry_type: str = "article"

    # Core bibliographic fields
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    journal: str = ""
    booktitle: str = ""
    publisher: str = ""
    volume: str = ""
    number: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""

    # Status flags
    has_abstract: bool = False
    malformed: bool = False
    malform_reason: str = ""

    def source_venue(self) -> str:
        """Return the most meaningful publication venue string."""
        return self.journal or self.booktitle or self.publisher or ""

    def author_string(self) -> str:
        """Return a comma-separated author string."""
        return ", ".join(self.authors)


@dataclass
class ParseResult:
    """Aggregated result from parsing a BibTeX file."""

    entries: list[BibEntry] = field(default_factory=list)
    total_raw: int = 0
    malformed_count: int = 0
    duplicate_titles: list[str] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def usable(self) -> list[BibEntry]:
        return [e for e in self.entries if not e.malformed]

    @property
    def with_abstract(self) -> list[BibEntry]:
        return [e for e in self.usable if e.has_abstract]

    @property
    def without_abstract(self) -> list[BibEntry]:
        return [e for e in self.usable if not e.has_abstract]


@dataclass
class FormatOptions:
    """User-selected formatting and export settings."""

    # Document metadata
    doc_title: str = "Bibliography Article Compendium"
    doc_subtitle: str = "Generated from Uploaded BibTeX File"
    custom_filename: str = "bibliography_compendium"

    # Typography
    font_family: str = "Calibri"
    body_size_pt: float = 10.5
    heading_size_pt: float = 13.0
    line_spacing: float = 1.15

    # Layout
    page_breaks_between: bool = False
    include_toc: bool = True
    include_summary: bool = True
    number_entries: bool = True

    # Filtering
    filter_mode: str = "all"          # "all" | "articles_conf" | "with_abstract"
    sort_mode: str = "alpha_title"    # "alpha_title" | "year_asc" | "year_desc" | "original"
