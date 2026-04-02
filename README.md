# BibBrief

**Turn your bibliography into a document you can actually read.**

BibBrief takes a BibTeX export — the kind you download from Scopus, Web of Science, or Zotero after a literature search — and converts it into a clean, structured Microsoft Word document. Every article gets its own entry: the title, a formatted reference, and the full abstract. 

---

## Try it now

**[bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app](https://bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app/)**

No installation required. Upload your file, generate the document, download it.

---

## Who it is for

BibBrief is built for researchers and students who regularly work with large collections of academic articles — particularly anyone doing:

- **Systematic literature reviews** — where you need to read and annotate dozens or hundreds of abstracts
- **Scoping reviews** — where a first pass through abstracts determines what gets read in full
- **Bibliography management** — where a readable, portable document is more useful than a raw database export
- **Research assistant workflows** — where articles need to be distributed or summarised in a common format
- **Thesis and dissertation work** — where a compiled reading list with abstracts saves significant time

If you have ever exported 500 references from Scopus and wished you had something more readable than a `.bib` file, BibBrief is for you.

---

## What it produces

BibBrief generates a polished Word document (`.docx`) with:

- A **cover page** with the document title, subtitle, and date
- A **table of contents** (populated automatically by Word when you open the file)
- A **numbered list of articles**, each containing:
  - **Title** — the full article title, preserved exactly
  - **Reference** — a cleanly formatted citation (authors, year, journal, volume, pages, DOI)
  - **Abstract** — the full abstract text, or a clear note if the abstract was not available in your source file
- A **processing summary** at the end, showing how many entries were included, how many abstracts were missing, and any entries that could not be parsed

The document is structured so it can be navigated easily in Word — you can jump between sections using the sidebar or table of contents.

---

## Core features

- **Handles large files.** BibBrief is designed for real-world literature searches. Files with up to approximately 6,000 entries are supported.
- **Flexible entry inclusion.** You can include all entries, restrict to journal articles and conference papers, or limit to entries that have an abstract.
- **Multiple sort options.** Sort alphabetically by title, by year (oldest or newest first), or preserve the original order from your export file.
- **Missing abstracts handled gracefully.** If an entry does not include an abstract, the document reads *Abstract: Not available.* — it is never silently blank.
- **Customisable document settings.** Choose the document title, subtitle, output filename, font family, body size, line spacing, and whether to include page breaks between articles.
- **Robust parsing.** BibBrief uses a two-pass strategy to recover entries that standard parsers miss, including entries with unusual formatting or non-standard fields.
- **Duplicate detection.** The processing summary flags titles that appear more than once in the source file.
- **No internet required for local use.** Once installed, BibBrief runs entirely on your machine.

---

## How to use it

**Using the deployed app (no installation needed):**

1. Go to [bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app](https://bibbrief-rexvitzkduhce2j9zitkgv.streamlit.app/)
2. Click the upload area and select your `.bib` file
3. Review the parse summary — it shows how many entries were found and how many have abstracts
4. Adjust any settings in the left sidebar (optional)
5. Click **Generate Word Document**
6. Click **Download Word Document** when the file is ready

The whole process typically takes 10–30 seconds for files up to 2,000 entries.

**When you open the downloaded document in Word:**
Right-click the table of contents area and select *Update Field* to populate it with page numbers.

---

## Supported file formats

BibBrief accepts standard `.bib` files exported from:

- **Scopus** — Export → BibTeX
- **Web of Science** — Export → BibTeX
- **Zotero** — File → Export Library → BibTeX
- **Mendeley** — File → Export → BibTeX
- **JabRef** — File → Export → BibTeX
- Any reference manager that produces standard BibTeX output

---

## Running locally

If you prefer to run BibBrief on your own machine:

**Requirements:** Python 3.9 or later

```bash
# 1. Download or clone the project
cd bib_to_docx_app

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Notes and limitations

- **Abstract availability depends on your source.** If Scopus or Web of Science did not include the abstract in your export, BibBrief cannot supply it. The quality of the output reflects the quality of the source metadata.
- **The table of contents requires one manual step.** After opening the Word document, right-click the TOC area and select *Update Field* to populate page numbers. This is a Word limitation, not a BibBrief one.
- **Very large files take longer.** A file with 4,000–6,000 entries may take 60–90 seconds to generate. Disabling *Page break between articles* (in the sidebar) speeds this up significantly.
- **Malformed entries may be skipped.** Entries with severe formatting problems in the source file may not parse correctly. The processing summary shows how many were affected.
- **BibBrief does not edit or summarise content.** Every title, reference, and abstract is reproduced exactly as it appears in the source file. BibBrief does not use AI to generate, paraphrase, or supplement any text.

---

## Project structure

```
bib_to_docx_app/
├── app.py                   — Application interface
├── requirements.txt         — Python dependencies
├── README.md
├── core/
│   ├── parser.py            — BibTeX parsing
│   ├── formatter.py         — Reference string construction
│   ├── document_builder.py  — Word document generation
│   ├── models.py            — Data structures
│   └── utils.py             — Shared helpers
└── assets/
    └── styles.css           — Interface styling
```

---

*BibBrief is an open utility for researchers. It does not store, transmit, or retain any uploaded files or generated documents.*
