"""
app.py — BibBrief
A research-grade bibliography-to-Word utility.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Backend modules — logic unchanged
from core.parser import parse_bib_content, filter_entries, sort_entries
from core.document_builder import build_docx
from core.models import FormatOptions, ParseResult
from core.utils import estimate_generation_time, entries_to_preview_rows, safe_filename

st.set_page_config(
    page_title="BibBrief",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = APP_DIR / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ── Caching (backend unchanged) ───────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cached_parse(content: str) -> ParseResult:
    return parse_bib_content(content)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> FormatOptions:
    opts = FormatOptions()

    with st.sidebar:
        st.markdown(
            "<div style='font-family:Georgia,serif;font-size:1.2rem;"
            "font-weight:500;color:#111;letter-spacing:-0.01em;"
            "margin-bottom:0.1rem;'>BibBrief</div>"
            "<div style='font-family:sans-serif;font-size:0.7rem;"
            "color:#AAA;margin-bottom:1.2rem;'>Settings &amp; Options</div>",
            unsafe_allow_html=True,
        )

        st.markdown('<span class="sidebar-section-label">Inclusion</span>',
                    unsafe_allow_html=True)
        opts.filter_mode = st.selectbox(
            "entry_filter",
            options=["all", "articles_conf", "with_abstract"],
            format_func=lambda x: {
                "all": "All entries",
                "articles_conf": "Articles & conference papers",
                "with_abstract": "Only entries with abstracts",
            }[x],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown('<span class="sidebar-section-label">Sorting</span>',
                    unsafe_allow_html=True)
        opts.sort_mode = st.selectbox(
            "sort_order",
            options=["alpha_title", "year_asc", "year_desc", "original"],
            format_func=lambda x: {
                "alpha_title": "Alphabetical by title",
                "year_asc":    "Year — oldest first",
                "year_desc":   "Year — newest first",
                "original":    "Original BibTeX order",
            }[x],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown('<span class="sidebar-section-label">Document</span>',
                    unsafe_allow_html=True)
        opts.doc_title = st.text_input("Document title",
                                        value="Bibliography Article Compendium")
        opts.doc_subtitle = st.text_input("Subtitle",
                                           value="Generated from Uploaded BibTeX File")
        opts.custom_filename = st.text_input("Output filename (no extension)",
                                              value="bibliography_compendium")

        st.markdown('<span class="sidebar-section-label">Typography</span>',
                    unsafe_allow_html=True)
        opts.font_family = st.selectbox(
            "Font family",
            options=["Calibri", "Aptos", "Times New Roman", "Garamond", "Arial"],
            index=0,
        )
        opts.body_size_pt = st.slider("Body font size (pt)",
                                       min_value=9.0, max_value=13.0,
                                       value=10.5, step=0.5)
        opts.line_spacing = st.select_slider("Line spacing",
                                              options=[1.0, 1.15, 1.5, 2.0],
                                              value=1.15)

        st.markdown('<span class="sidebar-section-label">Layout</span>',
                    unsafe_allow_html=True)
        opts.number_entries = st.checkbox("Number articles", value=True)
        opts.page_breaks_between = st.checkbox(
            "Page break between articles", value=False,
            help="Increases file size for large collections.")
        opts.include_toc = st.checkbox("Include table of contents", value=True)
        opts.include_summary = st.checkbox("Include processing summary", value=True)

        st.markdown('<span class="sidebar-section-label">About BibBrief</span>',
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.76rem;color:#BBBBBB;line-height:1.7;"
            "font-family:sans-serif;'>"
            "Converts <code>.bib</code> exports from Scopus, Web of Science, "
            "Zotero, and other reference managers into clean Word documents."
            "<br><br>Handles up to ~6,000 entries."
            "</div>",
            unsafe_allow_html=True,
        )

    return opts


# ── Stat cards ─────────────────────────────────────────────────────────────────

def _stat_card(value: str, label: str, variant: str = "") -> str:
    cls = f"stat-card {variant}".strip()
    return (
        f'<div class="{cls}">'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f'</div>'
    )


def render_stats(result: ParseResult, included_count: int) -> None:
    cards = [
        _stat_card(f"{result.total_raw:,}",             "Total entries",       ""),
        _stat_card(f"{included_count:,}",                "Included",            "accent"),
        _stat_card(f"{len(result.with_abstract):,}",     "With abstract",       ""),
        _stat_card(f"{len(result.without_abstract):,}",  "Missing abstract",    ""),
        _stat_card(f"{result.malformed_count:,}",        "Malformed / skipped", "muted"),
        _stat_card(f"{len(result.duplicate_titles):,}",  "Duplicate titles",    "muted"),
    ]
    st.markdown(
        '<div class="stat-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


# ── Main page ──────────────────────────────────────────────────────────────────

def main() -> None:
    opts = render_sidebar()

    # Hero
    st.markdown(
        """<div class="bibbrief-hero">
          <div class="bibbrief-wordmark">Bib<span>Brief</span></div>
          <div class="bibbrief-tagline">
            Transform large BibTeX libraries into clean, structured Word documents.
          </div>
          <div class="bibbrief-description">
            Upload a <code>.bib</code> file from Scopus, Web of Science, Zotero,
            or any compatible reference manager. BibBrief parses every entry and
            generates a polished, navigable document — title, reference, and
            abstract for each article.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Upload
    st.markdown('<span class="section-heading">Upload your bibliography</span>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="upload-container">'
        '<div class="upload-heading">Select a BibTeX file (.bib)</div>'
        '<div class="upload-hint">Large collections with thousands of entries are supported. '
        'The document generation step may take 20–60 seconds for very large files.</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "bib_upload", type=["bib"], label_visibility="collapsed"
    )

    if uploaded is None:
        st.markdown(
            '<div class="warning-banner">'
            "No file selected — upload a <strong>.bib</strong> file above to begin."
            "</div>",
            unsafe_allow_html=True,
        )
        _footer()
        return

    # Validate
    raw_bytes = uploaded.read()
    if not raw_bytes:
        st.error("The uploaded file is empty. Please upload a non-empty .bib file.")
        return
    try:
        content = raw_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        st.error(f"Could not read the file: {exc}")
        return
    if not content.strip().startswith("Scopus") and "@" not in content:
        st.error(
            "This file does not appear to contain valid BibTeX entries. "
            "Please verify the file format."
        )
        return

    # Parse
    with st.spinner("Parsing bibliography…"):
        t0 = time.perf_counter()
        result = cached_parse(content)
        elapsed = time.perf_counter() - t0

    if not result.entries:
        st.error(
            "The file could not be parsed as valid BibTeX. "
            "Please check the format and try again."
        )
        return

    # Filter + sort (backend logic unchanged)
    filtered       = filter_entries(result, opts.filter_mode)
    sorted_entries = sort_entries(filtered, opts.sort_mode)

    if not sorted_entries:
        st.warning(
            "No entries match the current filter. "
            "Adjust the inclusion setting in the sidebar."
        )
        return

    # Summary metrics
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<span class="section-heading">Parse summary</span>',
                unsafe_allow_html=True)
    render_stats(result, len(sorted_entries))
    st.caption(
        f"Parsed in {elapsed:.2f}s · {len(result.parse_errors)} parse warning(s)"
    )
    if result.parse_errors:
        with st.expander(f"Parse warnings ({len(result.parse_errors)})"):
            for err in result.parse_errors[:30]:
                st.markdown(
                    f"<small style='color:#AAAAAA'>{err}</small>",
                    unsafe_allow_html=True,
                )

    # Entry preview
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<span class="section-heading">Entry preview</span>',
                unsafe_allow_html=True)
    preview_limit = 25
    preview_rows  = entries_to_preview_rows(sorted_entries, preview_limit)
    if preview_rows:
        st.markdown('<div class="preview-wrapper">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if len(sorted_entries) > preview_limit:
            st.caption(f"Showing {preview_limit} of {len(sorted_entries):,} included entries.")

    year_counts: dict[str, int] = {}
    for e in sorted_entries:
        if e.year:
            year_counts[e.year] = year_counts.get(e.year, 0) + 1
    if year_counts:
        with st.expander("Year distribution"):
            top_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            st.dataframe(pd.DataFrame(top_years, columns=["Year", "Count"]),
                         use_container_width=True, hide_index=True)

    total_with_authors = sum(1 for e in sorted_entries if e.authors)
    if total_with_authors:
        with st.expander("Author frequency"):
            all_authors: list[str] = []
            for e in sorted_entries:
                all_authors.extend(e.authors)
            top_authors = Counter(all_authors).most_common(20)
            st.dataframe(
                pd.DataFrame(top_authors, columns=["Author", "Appearances"]),
                use_container_width=True, hide_index=True,
            )

    # Generate
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<span class="section-heading">Generate document</span>',
                unsafe_allow_html=True)
    est = estimate_generation_time(len(sorted_entries))
    st.markdown(
        f'<div class="generate-area">'
        f'<div class="generate-meta">'
        f'<strong>{len(sorted_entries):,} entries</strong> will be included. '
        f'Estimated time: <strong>{est}</strong>. '
        f'For large files, disabling page breaks (sidebar) speeds things up.'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button("Generate Word Document", type="primary"):
        progress_bar = st.progress(0.0, text="Building document…")
        status_slot  = st.empty()

        def update_progress(fraction: float) -> None:
            progress_bar.progress(
                min(fraction, 1.0),
                text=f"Building document… {int(fraction * 100)}%",
            )

        gen_start = time.perf_counter()
        try:
            docx_bytes = build_docx(
                entries=sorted_entries,
                result=result,
                opts=opts,
                progress_callback=update_progress,
            )
            gen_elapsed = time.perf_counter() - gen_start
            progress_bar.progress(1.0, text="Complete ✓")
            status_slot.empty()

            st.markdown(
                f'<div class="success-banner">'
                f"Document generated in {gen_elapsed:.1f}s — "
                f"<strong>{len(sorted_entries):,} entries</strong> included, "
                f"{len(result.without_abstract):,} without abstracts."
                f"</div>",
                unsafe_allow_html=True,
            )

            st.session_state["docx_bytes"]    = docx_bytes
            st.session_state["docx_filename"] = safe_filename(opts.custom_filename) + ".docx"
            st.session_state["docx_size_kb"]  = len(docx_bytes) / 1024

        except Exception as exc:
            progress_bar.empty()
            st.error(
                f"Document generation failed: {exc}\n\n"
                "Try again, or reduce included entries via the sidebar filter."
            )
            raise

    st.markdown("</div>", unsafe_allow_html=True)

    # Download
    if "docx_bytes" in st.session_state:
        size_kb  = st.session_state.get("docx_size_kb", 0)
        filename = st.session_state.get("docx_filename", "bibliography.docx")
        st.markdown(
            '<div class="download-area">'
            '<span class="download-label">Your document is ready</span>',
            unsafe_allow_html=True,
        )
        st.download_button(
            label="Download Word Document",
            data=st.session_state["docx_bytes"],
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.markdown(
            f'<div class="download-meta">{filename} &nbsp;·&nbsp; {size_kb:,.0f} KB</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    _footer()


def _footer() -> None:
    st.markdown(
        '<div class="bibbrief-footer">'
        "BibBrief &nbsp;·&nbsp; "
        '<a href="https://bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app/" '
        'target="_blank">bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app</a>'
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
