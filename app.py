"""
app.py — BibTeX → DOCX Streamlit Application

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

from core.parser import parse_bib_content, filter_entries, sort_entries
from core.document_builder import build_docx
from core.models import FormatOptions, ParseResult
from core.utils import estimate_generation_time, entries_to_preview_rows, safe_filename

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BibTeX → DOCX",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────
css_path = APP_DIR / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Caching
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cached_parse(content: str) -> ParseResult:
    """Parse BibTeX content (cached so re-runs don't re-parse)."""
    return parse_bib_content(content)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> FormatOptions:
    opts = FormatOptions()

    with st.sidebar:
        st.markdown("## Filtering")
        filter_choice = st.selectbox(
            "Include entries",
            options=["all", "articles_conf", "with_abstract"],
            format_func=lambda x: {
                "all":           "All entries",
                "articles_conf": "Articles & conference papers",
                "with_abstract": "Only entries with abstracts",
            }[x],
            index=0,
        )
        opts.filter_mode = filter_choice

        st.markdown("## Sorting")
        sort_choice = st.selectbox(
            "Sort order",
            options=["alpha_title", "year_asc", "year_desc", "original"],
            format_func=lambda x: {
                "alpha_title": "Alphabetical by title",
                "year_asc":    "Year — oldest first",
                "year_desc":   "Year — newest first",
                "original":    "Original BibTeX order",
            }[x],
            index=0,
        )
        opts.sort_mode = sort_choice

        st.markdown("## Document")
        opts.doc_title = st.text_input(
            "Document title",
            value="Bibliography Article Compendium",
        )
        opts.doc_subtitle = st.text_input(
            "Subtitle",
            value="Generated from Uploaded BibTeX File",
        )
        opts.custom_filename = st.text_input(
            "Output filename (no extension)",
            value="bibliography_compendium",
        )

        st.markdown("## Typography")
        opts.font_family = st.selectbox(
            "Font family",
            options=["Calibri", "Aptos", "Times New Roman", "Garamond", "Arial"],
            index=0,
        )
        opts.body_size_pt = st.slider(
            "Body font size (pt)",
            min_value=9.0, max_value=13.0, value=10.5, step=0.5,
        )
        opts.line_spacing = st.select_slider(
            "Line spacing",
            options=[1.0, 1.15, 1.5, 2.0],
            value=1.15,
        )

        st.markdown("## Layout")
        opts.number_entries = st.checkbox("Number articles", value=True)
        opts.page_breaks_between = st.checkbox(
            "Page break between articles", value=False,
            help="Significantly increases file size for large collections.",
        )
        opts.include_toc = st.checkbox("Include table of contents", value=True)
        opts.include_summary = st.checkbox("Include processing summary", value=True)

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.75rem;color:#AAAAAA;line-height:1.6'>"
            "<strong>BibTeX → DOCX</strong><br>"
            "Converts Scopus/Web of Science/<br>Zotero .bib exports to<br>"
            "polished Word documents.<br><br>"
            "Handles files up to ~6,000 entries."
            "</div>",
            unsafe_allow_html=True,
        )

    return opts


# ─────────────────────────────────────────────────────────────────────────────
# Stat cards
# ─────────────────────────────────────────────────────────────────────────────

def stat_card(value: int | str, label: str) -> str:
    return (
        f'<div class="stat-card">'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f'</div>'
    )


def render_stats(result: ParseResult, included_count: int) -> None:
    cards = [
        stat_card(f"{result.total_raw:,}",       "Total entries"),
        stat_card(f"{included_count:,}",          "Included"),
        stat_card(f"{len(result.with_abstract):,}", "With abstract"),
        stat_card(f"{len(result.without_abstract):,}", "Missing abstract"),
        stat_card(f"{result.malformed_count:,}",  "Malformed / skipped"),
        stat_card(f"{len(result.duplicate_titles):,}", "Duplicate titles"),
    ]
    html = '<div class="stat-grid">' + "".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    opts = render_sidebar()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<h1 class="app-title">BibTeX → Word Document</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="app-subtitle">'
        "Upload a <code>.bib</code> file exported from Scopus, Web of Science, "
        "Zotero, or any BibTeX-compatible reference manager. "
        "The app parses all entries and generates a polished, navigable Word document "
        "containing the title, reference, and abstract of each article."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload BibTeX file",
        type=["bib"],
        help="Accepts standard .bib files. Large files (up to ~6,000 entries) are supported.",
        label_visibility="collapsed",
    )

    if uploaded is None:
        st.markdown(
            '<div class="warning-banner">'
            "No file selected. Upload a <strong>.bib</strong> file to begin."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Validate ──────────────────────────────────────────────────────────────
    raw_bytes = uploaded.read()
    if not raw_bytes:
        st.error("The uploaded file is empty. Please upload a non-empty .bib file.")
        return

    try:
        content = raw_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"Could not read file contents: {e}")
        return

    if not content.strip().startswith("Scopus") and "@" not in content:
        st.error(
            "The uploaded file does not appear to contain valid BibTeX entries. "
            "Please verify the file format."
        )
        return

    # ── Parse ─────────────────────────────────────────────────────────────────
    with st.spinner("Parsing bibliography…"):
        t0 = time.perf_counter()
        result = cached_parse(content)
        elapsed = time.perf_counter() - t0

    if not result.entries:
        st.error(
            "The uploaded file could not be parsed as valid BibTeX. "
            "Please check the file format and try again."
        )
        return

    # ── Apply filter + sort ───────────────────────────────────────────────────
    filtered = filter_entries(result, opts.filter_mode)
    sorted_entries = sort_entries(filtered, opts.sort_mode)

    if not sorted_entries:
        st.warning(
            "No entries match the current filter settings. "
            "Try changing the filter in the sidebar."
        )
        return

    # ── Parse summary ─────────────────────────────────────────────────────────
    st.markdown("<hr class='section-rule'>", unsafe_allow_html=True)
    st.markdown("## Parse Summary")
    render_stats(result, len(sorted_entries))

    st.caption(f"Parsed in {elapsed:.2f}s · {len(result.parse_errors)} parse warning(s)")

    if result.parse_errors:
        with st.expander(f"Parse warnings ({len(result.parse_errors)})"):
            for e in result.parse_errors[:30]:
                st.markdown(f"<small style='color:#999'>{e}</small>", unsafe_allow_html=True)

    # ── Preview table ─────────────────────────────────────────────────────────
    st.markdown("<hr class='section-rule'>", unsafe_allow_html=True)
    st.markdown("## Entry Preview")

    preview_limit = 25
    preview_rows = entries_to_preview_rows(sorted_entries, preview_limit)

    if preview_rows:
        df = pd.DataFrame(preview_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if len(sorted_entries) > preview_limit:
            st.caption(
                f"Showing first {preview_limit} of {len(sorted_entries):,} included entries."
            )

    # Year distribution
    year_counts: dict[str, int] = {}
    for e in sorted_entries:
        if e.year:
            year_counts[e.year] = year_counts.get(e.year, 0) + 1

    if year_counts:
        with st.expander("Year distribution"):
            top_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            df_years = pd.DataFrame(top_years, columns=["Year", "Count"])
            st.dataframe(df_years, use_container_width=True, hide_index=True)

    # Author count
    total_with_authors = sum(1 for e in sorted_entries if e.authors)
    if total_with_authors:
        with st.expander("Author statistics"):
            all_authors: list[str] = []
            for e in sorted_entries:
                all_authors.extend(e.authors)
            from collections import Counter
            top_authors = Counter(all_authors).most_common(20)
            df_auth = pd.DataFrame(top_authors, columns=["Author", "Appearances"])
            st.dataframe(df_auth, use_container_width=True, hide_index=True)

    # ── Generate ──────────────────────────────────────────────────────────────
    st.markdown("<hr class='section-rule'>", unsafe_allow_html=True)
    st.markdown("## Generate Word Document")

    est = estimate_generation_time(len(sorted_entries))
    st.caption(
        f"{len(sorted_entries):,} entries will be included. "
        f"Estimated generation time: **{est}**."
    )

    if st.button("Generate Word Document", type="primary"):
        progress_bar = st.progress(0.0, text="Building document…")
        status_text  = st.empty()

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

            progress_bar.progress(1.0, text="Complete!")
            status_text.empty()

            st.markdown(
                f'<div class="success-banner">'
                f"✓ Document generated in {gen_elapsed:.1f}s — "
                f"{len(sorted_entries):,} entries, "
                f"{len(result.without_abstract):,} missing abstracts."
                f"</div>",
                unsafe_allow_html=True,
            )

            # Store in session state for download persistence
            st.session_state["docx_bytes"]    = docx_bytes
            st.session_state["docx_filename"] = (
                safe_filename(opts.custom_filename) + ".docx"
            )

        except Exception as exc:
            progress_bar.empty()
            st.error(
                f"Document generation failed: {exc}\n\n"
                "Please try again. If the problem persists, reduce the number "
                "of entries using the sidebar filter."
            )
            raise

    # ── Download ──────────────────────────────────────────────────────────────
    if "docx_bytes" in st.session_state:
        st.markdown("---")
        st.download_button(
            label="⬇  Download Word Document",
            data=st.session_state["docx_bytes"],
            file_name=st.session_state.get("docx_filename", "bibliography.docx"),
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )

        total_kb = len(st.session_state["docx_bytes"]) / 1024
        st.caption(f"File size: {total_kb:,.0f} KB")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
