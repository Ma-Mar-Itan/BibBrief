"""
formatter.py — Reference string construction from BibEntry metadata.

Produces clean academic-style references without exposing raw BibTeX syntax.
"""
from __future__ import annotations

from .models import BibEntry


def format_reference(entry: BibEntry) -> str:
    """
    Build a clean, APA-adjacent reference string from available metadata.

    Construction order:
      Authors (Year). Title. Venue, Volume(Number), Pages. DOI/URL
    """
    parts: list[str] = []

    # Authors
    if entry.authors:
        author_str = ", ".join(entry.authors)
        parts.append(author_str)

    # Year
    year_part = f"({entry.year})" if entry.year else ""
    if year_part:
        parts.append(year_part + ".")
    elif parts:
        parts[-1] += "."  # punctuate last token

    # Title
    if entry.title:
        parts.append(f"{entry.title}.")

    # Venue (journal / booktitle / publisher)
    venue = entry.source_venue()
    if venue:
        venue_str = venue

        # Volume and number
        if entry.volume:
            venue_str += f", {entry.volume}"
            if entry.number:
                venue_str += f"({entry.number})"

        # Pages
        if entry.pages:
            venue_str += f", {entry.pages}"

        venue_str += "."
        parts.append(venue_str)

    # DOI / URL
    if entry.doi:
        parts.append(f"https://doi.org/{entry.doi}")
    elif entry.url:
        parts.append(entry.url)

    if not parts:
        return "Reference information not available."

    return " ".join(parts)
