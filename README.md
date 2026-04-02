# BibTeX → Word Document

A production-quality Streamlit application that converts `.bib` bibliography
files into polished Microsoft Word documents (`.docx`).

Designed for researchers, librarians, and academics who need a clean, navigable
document from large BibTeX exports (Scopus, Web of Science, Zotero, etc.).

---

## Features

- **Robust parsing** — two-pass strategy (bibtexparser + regex fallback) recovers
  virtually all entries from messy or partially malformed BibTeX files
- **Large file support** — tested up to 6,000 entries
- **Polished DOCX output** — cover page, table of contents, structured article
  blocks (title → reference → abstract), processing summary
- **Missing abstract handling** — entries without abstracts display
  "Abstract: Not available."
- **Flexible filtering** — all entries, articles & conference papers only,
  or only entries with abstracts
- **Multiple sort orders** — alphabetical, year ascending/descending, original order
- **Typography settings** — font family, size, line spacing
- **Clean, minimal UI** — white, restrained, academic aesthetic

---

## Requirements

- Python 3.9 or later
- pip

---

## Installation

### 1. Clone or download the project

```bash
git clone <repo-url>
cd bib_to_docx_app
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your default browser.

---

## Supported Input Format

Standard BibTeX (`.bib`) files exported from:
- Scopus
- Web of Science
- Zotero
- Mendeley
- JabRef
- Any BibTeX-compatible reference manager

The file may contain any combination of entry types:
`@article`, `@inproceedings`, `@conference`, `@book`, `@misc`,
`@incollection`, `@phdthesis`, `@mastersthesis`, `@techreport`, etc.

---

## Workflow

1. Open the app in your browser
2. Upload your `.bib` file via the upload area
3. Review the parse summary (total entries, abstracts, malformed entries)
4. Adjust filtering, sorting, and formatting options in the sidebar
5. Click **Generate Word Document**
6. Download the `.docx` file

---

## Output Document Structure

| Section | Contents |
|---|---|
| Cover page | Title, subtitle, date, entry count |
| Table of Contents | Word field — update in Word to populate |
| Articles (1–N) | Title → Reference → Abstract per entry |
| Processing Summary | Stats, duplicate titles, parse warnings |

---

## Known Limitations

- The table of contents field must be updated manually in Microsoft Word
  (right-click → Update Field) to populate page numbers.
- Very large files (>4,000 entries) with page breaks enabled between articles
  may produce large `.docx` files (>10 MB) and take 2–3 minutes to generate.
- BibTeX files with deeply nested or escaped braces in field values may not
  parse perfectly — the regex fallback handles most cases but cannot guarantee
  100% fidelity on severely malformed files.
- The app runs in a single process; concurrent users on a shared server may
  experience slower generation times.

---

## Troubleshooting

**"No entries match the current filter settings"**
→ Change the filter in the sidebar to "All entries".

**"The uploaded file does not appear to contain valid BibTeX entries"**
→ Verify the file extension is `.bib` and that it contains `@article{...}` style entries.

**Generation is very slow**
→ Disable "Page break between articles" in the sidebar. This significantly
reduces document size and build time for large collections.

**Abstract shows "Not available."**
→ The source entry did not include an `abstract` field. This is normal for
many BibTeX exports. No data is lost — the reference information is still included.

**Word document TOC is empty**
→ Open the document in Microsoft Word, select the TOC area, right-click,
and choose "Update Field" → "Update entire table".

---

## Project Structure

```
bib_to_docx_app/
├── app.py                  ← Streamlit application entry point
├── requirements.txt
├── README.md
├── core/
│   ├── __init__.py
│   ├── models.py           ← BibEntry, ParseResult, FormatOptions dataclasses
│   ├── parser.py           ← BibTeX parsing (two-pass)
│   ├── formatter.py        ← Reference string construction
│   ├── document_builder.py ← DOCX generation (python-docx)
│   └── utils.py            ← Shared helpers
└── assets/
    └── styles.css          ← Custom Streamlit CSS
```
