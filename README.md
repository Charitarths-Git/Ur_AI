# jp-balance-sheet-parser

Parse Japanese consolidated balance sheets (連結貸借対照表) from PDF into structured CSV and JSON.

> **Status**: P1 — PDF inspection complete. See [notes/inspection.md](notes/inspection.md) for findings.

## Quick start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd jp-balance-sheet-parser

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies (exact versions)
pip install -r requirements.lock

# 3b. Or install with flexible versions (editable, for development)
pip install -e ".[dev]"

# 4. Run tests
pytest
```

## Repository layout

```
├── src/
│   └── parser/            # Main Python package
│       └── __init__.py
├── tests/                 # Pytest test suite
├── scripts/               # CLI entry points and utilities
│   └── inspect_pdf.py     # PDF diagnostic tool (P1)
├── data/
│   ├── raw/               # Original PDFs (tracked in git)
│   ├── gt/                # Hand-labeled ground-truth files
│   └── derived/           # Rendered images, derived artifacts (tracked)
├── outputs/               # Generated CSV / JSON (git-ignored)
├── eval/                  # Evaluation scripts and configs
├── notes/                 # Inspection findings and design notes
├── PROJECT_BRIEF.md       # Full task description and plan
├── workstamp.md           # Session handoff state (read this first!)
├── pyproject.toml         # Python project metadata and deps
└── requirements.lock      # Pinned dependency versions (pip freeze)
```

## Phases

| Phase | Scope |
|---|---|
| P0 — Setup | Repository layout, dependencies, smoke test ✅ |
| P1 — Inspect the PDF | Diagnostic extraction; understand text layer and layout ✅ |
| P2 — Ground truth | Hand-verified table from rendered page image |
| P3 — Normalization | Full-width→half-width, △, －, commas; with tests |
| P4 — Row reconstruction | Cluster words into rows, assign columns |
| P5 — Hierarchy inference | Parent-path assignment from indentation + rules |
| P6 — CSV and JSON export | Generate flat CSV and hierarchical JSON |
| P7 — Evaluation metrics | Cell accuracy, structural accuracy, accounting checks |
| P8 — End-to-end run | Failure analysis and robustness testing |
| P9 — Independent review | Review by a different AI agent |
| P10 — Review fixes | Apply fixes from the review |
| P11 — Write-up | Report with design decisions, results, future work |
| P12 — OCR/VLM stub | Optional backend stub for scanned pages |
| P13 — Reproducibility | Clean-clone reproducibility verification |

## Dependencies

| Package | Purpose |
|---|---|
| PyMuPDF | Low-level PDF text + coordinate extraction |
| pdfplumber | Higher-level table / layout extraction |
| pandas | Tabular data manipulation and CSV output |
| pytest | Test runner |
| ruff | Linter / formatter |

## Scripts

### `scripts/inspect_pdf.py`

Diagnostic tool that extracts and dumps all text, coordinates, and drawings from the PDF. Not a parser.

```bash
# Run with the venv activated:
# On Windows, set encoding first to avoid console errors:
set PYTHONIOENCODING=utf-8   # cmd
$env:PYTHONIOENCODING="utf-8" # PowerShell

python scripts/inspect_pdf.py data/raw/balance_sheet_after_correction.pdf

# Output files written to notes/:
#   words_pymupdf.json    — every word with bbox, font, size (PyMuPDF)
#   words_pdfplumber.json — every word with bbox (pdfplumber)
#   drawings.json         — vector elements (lines, rects)
#
# Also renders page 1 to:
#   data/derived/page4_200dpi.png  (200 DPI PNG; used for ground-truth in P2)
```

## License

This project is a take-home assignment and is not licensed for redistribution.
