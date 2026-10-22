# jp-balance-sheet-parser

Parse Japanese consolidated balance sheets (連結貸借対照表) from PDF into structured CSV and JSON.

> **Status**: P3 — normalization utilities and tests complete. P2 ground truth is **VERIFIED**.
> Next phase: P4 row reconstruction.

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
│       ├── __init__.py
│       └── normalize.py   # Pure amount, label-matching and period helpers (P3)
├── tests/                 # Pytest test suite
├── scripts/               # CLI entry points and utilities
│   └── inspect_pdf.py     # PDF diagnostic tool (P1)
├── data/
│   ├── raw/               # Original PDFs (tracked in git)
│   ├── gt/                # VERIFIED image-transcribed CSV, metadata and conventions (P2)
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
| P2 — Ground truth | Image-derived GT verified by human, no corrections ✅ |
| P3 — Normalization | Pure amount, label-matching and period helpers with tests ✅ |
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

## Verified ground truth (P2)

`data/gt/page4.csv` contains one row per printed body row in reading order,
from 資産の部 through 資産合計. It is UTF-8 with BOM and retains raw printed
strings alongside integer 千円 values, semantic parents and ancestor paths.
Printed `－` cells have empty values; `△0` has value 0 with its raw sign retained.
See [data/gt/README.md](data/gt/README.md) for the exact conventions and
[data/gt/page4_meta.json](data/gt/page4_meta.json) for page and period metadata.

This GT is **VERIFIED**: `verified_by_human` is true. The user confirmed all
43 rows against the page image, including hierarchy columns, and reported an
independent second review with no discrepancies. The completed checklist is in
[notes/gt_verification.md](notes/gt_verification.md). The CSV was committed before the text-layer check.
Arithmetic differences and text-layer checks never authorize automatic GT edits.
The captured diagnostics are in [notes/p2_report.md](notes/p2_report.md).

With the venv active (PowerShell: `$env:PYTHONIOENCODING="utf-8"`):

```bash
python scripts/gt_selfcheck.py
python scripts/gt_crosscheck.py
# Optional: regenerate overlapping 300 DPI visual aids (rendering only)
python scripts/render_gt_crops.py
python -m pytest
```

`gt_selfcheck.py` validates the schema and reports component sums, printed values
and differences for every net/subtotal/total, in 千円. It lists omitted null
components without changing them to zero. Arithmetic is **information only**:
there is no financial pass/fail or tolerance logic (reserved for P7).
`gt_crosscheck.py` reads numeric/nil tokens from the PDF text layer and compares
both raw strings and values by column and vertical order. It uses page-specific
body bounds, excludes headings/footer, reports disagreements and never writes GT.
Both scripts are throwaway verification aids outside `src/`, not package code.

## Normalization (P3)

The stdlib-only helpers in `src/parser/normalize.py` are pure and do not access
PDFs or infer rows, hierarchy or accounting roles:

- `parse_amount(raw) -> AmountResult`: returns a frozen result with the exact
  raw input, integer/null value, status (`ok`, `nil`, `invalid`, `empty`), negative
  flag and note. Units remain 千円; no scaling is applied. Full-width digits and
  commas, negative signs and parentheses are supported. A standalone dash run
  is nil (`None`), while printed `△0` is integer zero with `negative=True` and
  note `negative zero printed`. Empty and invalid inputs remain distinct from nil
  and never become zero. Non-string amount inputs are invalid.
- `label_key(label) -> str` and `labels_equal(a, b) -> bool`: NFKC comparison
  with all Unicode whitespace removed. **label_key is for matching only**;
  output labels retain their exact printed form, including full-width （純額）.
- `parse_period_end(text) -> tuple[int, int, int] | None`: extracts the first
  complete Gregorian date, allowing full-width digits and arbitrary spaces.
  Missing or impossible dates return `None`. Japanese-era (和暦) dates are unsupported.

Decimals and unit suffixes are invalid because amounts are whole printed 千円.
All listed nil dash variants can also serve as a single negative prefix before
digits. Whitespace after a sign or inside parentheses is allowed; whitespace
between digits, repeated signs and signed parentheses are invalid. Nonempty
comma groups of unusual widths are accepted with an informational note; leading,
trailing or repeated commas are invalid. Very long integers are supported without
changing Python's global conversion limits. Further decisions are documented in
the module docstring.

```bash
python -m pytest tests/test_normalize.py
python -m pytest
python -m ruff check src/parser/normalize.py tests/test_normalize.py
```

The GT round-trip test reads the verified CSV with `utf-8-sig`, compares every
previous/current raw cell with its stored value, and checks nil/header statuses.
It neither writes GT nor accesses the PDF.

## License

This project is a take-home assignment and is not licensed for redistribution.
