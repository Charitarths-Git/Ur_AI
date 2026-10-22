# jp-balance-sheet-parser

Parse Japanese consolidated balance sheets (連結貸借対照表) from PDF into structured CSV and JSON.

> **Status**: P5–P6 — row types, hierarchy, metadata and CSV/JSON export complete. GT is **VERIFIED**.
> Next phase: P7–P8 evaluation framework.

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
│       ├── normalize.py   # Pure amount, label-matching and period helpers (P3)
│       ├── layout_types.py # Frozen raw/layout structures and relative thresholds (P4)
│       ├── pdf_backend.py # Replaceable PDF reader; package's only PyMuPDF import (P4)
│       ├── rows.py        # Pure visual reconstruction; no hierarchy or semantic roles (P4)
│       ├── rules.py       # Replaceable language patterns (P5)
│       ├── classify.py    # Row types, independent evidence and typed warnings (P5)
│       ├── hierarchy.py   # Parent stack, paths and partial flat fallback (P5)
│       ├── metadata.py    # Page metadata and chronological column roles (P5)
│       └── export.py      # Parsed-page pipeline and deterministic CSV/JSON (P6)
├── tests/                 # Pytest test suite
├── scripts/               # CLI entry points and utilities
│   ├── inspect_pdf.py     # PDF diagnostic tool (P1)
│   ├── dump_rows.py       # Text diagnostic for rows, columns and layout evidence (P4)
│   ├── parse_page.py      # PDF → typed tree → CSV and JSON (P5–P6)
│   └── _console.py        # UTF-8 stdout/stderr startup shared by CLI scripts
├── data/
│   ├── raw/               # Original PDFs (tracked in git)
│   ├── gt/                # VERIFIED image-transcribed CSV, metadata and conventions (P2)
│   └── derived/           # Rendered images, derived artifacts (tracked)
├── outputs/               # Generated CSV / JSON (git-ignored)
├── examples/              # Committed real-page CSV and hierarchical JSON
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
| P4 — Row reconstruction | Relative row/column reconstruction, visual indent steps and rule evidence ✅ |
| P5 — Hierarchy inference | Typed rows, parent paths, metadata and partial fallback ✅ |
| P6 — CSV and JSON export | Deterministic flat CSV and hierarchical JSON; committed examples ✅ |
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

## Visual row reconstruction (P4)

```bash
python scripts/dump_rows.py data/raw/balance_sheet_after_correction.pdf
python scripts/dump_rows.py data/raw/balance_sheet_after_correction.pdf --page 1
```

`--page` is the one-based PDF page index (the input file's first page is printed
as page 4). The command prints every row's zone, y bounds, raw label and cells,
visual indent step and rule flag, then column/date and threshold evidence.
All CLI scripts configure stdout/stderr as UTF-8 automatically; encoding
environment variables are no longer required to print Japanese text.

`parser.pdf_backend.read_pdf_page(path, page_number=1, config=LayoutConfig())`
returns a backend-neutral `RawPage`. `PageBackend` is the interface for future
OCR/VLM readers; only the default backend is implemented.
`parser.rows.reconstruct_page(raw_page, config=LayoutConfig()) -> PageLayout`
is pure and returns frozen rows, columns, cells, indent centres and thresholds.
`parser.layout_types` defines these structures and the configurable relative
thresholds. Pass the same config to the reader and reconstruction when changing
rule limits. No fixed page coordinates or table row counts are used.

Columns come from repeated right edges across distinct rows, not token meaning.
Aligned invalid amounts remain cells. Labels preserve extracted text and use
geometric spaces; indent steps are raw visual clusters. Header/footer zones and
horizontal rules are structural evidence. Parent paths, semantic levels and row
types are supplied by the P5 stage below; P4 does not export CSV/JSON or calculate evaluation
metrics. The P3 normalization module is unchanged.

See [notes/row_reconstruction.md](notes/row_reconstruction.md) for the algorithm,
all threshold defaults and actual page values, GT comparison, informational
cross-tabs, transformation tests and limitations. In particular, wrapped labels,
page-spanning/multiple tables, grouped headings and label-only boundary rows
need further work. Rotated pages are rejected; scanned text requires a future
backend.

```bash
python -m pytest tests/test_rows.py
python -m pytest
python -m ruff check src/parser/layout_types.py src/parser/pdf_backend.py src/parser/rows.py scripts tests/test_rows.py
```

## Full parsing and export pipeline (P5–P6)

```text
PDF → RawPage → PageLayout → classified rows → parent tree + metadata → CSV/JSON
```

```bash
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf --page 1 --out-dir outputs
```

`--page` is one-based within the PDF. Outputs are named
`balance_sheet_after_correction_p1.csv` and `.json`; the summary reports types,
hierarchy source and warnings. UTF-8 console configuration is automatic.
Identical committed samples are in [examples/](examples/). Only the supplied
printed page 4 has been validated against real-document GT.

The public PDF entry point is:

```python
from parser.export import parse_page
from parser.layout_types import LayoutConfig
from parser.rules import JA_FINANCIAL_STATEMENT

page = parse_page(path, page_number=1, layout_config=LayoutConfig(),
                  rules=JA_FINANCIAL_STATEMENT)
```

For an already reconstructed layout, `parse_layout(layout, source_name, ...)`
performs pure assembly. `classify_rows`, `build_hierarchy` and `extract_metadata`
are pure stages. `csv_bytes` and `json_bytes` return deterministic bytes;
`write_exports(page, out_dir)` is the explicit file-writing boundary. ParsedPage
is frozen and holds flat reading-order rows, a root forest, page metadata,
role-bearing columns, typed warnings and hierarchy_source.

Language-specific matching lives in the frozen RuleSet. The Japanese default
contains total labels, subtotal/net suffixes, contra prefixes, unit patterns/map,
correction markers and the page-number pattern. Matching uses label_key while
output labels retain their exact printed form. Liability/equity labels, other
units and other unobserved patterns remain untested real-document heuristics.
See [notes/hierarchy_and_export.md](notes/hierarchy_and_export.md) for every
pattern's validation status, independent evidence counts and limitations.

With at least two visual indent steps, a preceding-row stack determines parents;
level counts ancestors. Otherwise a deliberately partial, warned rules fallback
is used. It cannot recover unknown header nesting. Conflicting label/evidence
signals emit warnings without overriding the label type. Structural type_source
and evidence remain available via each parsed row's `.typed` record.

Page metadata comes from header/footer zones. Exported column headings exclude
unit lines. Exactly two distinct dates determine previous/current roles by date,
otherwise columns use value_1..value_N and warn. Unit multipliers are metadata
only: financial values are never scaled.

The CSV uses **UTF-8 with BOM**, with this exact column order:

```text
label,parent,level,row_type,previous_year_value,current_year_value,row_id,parent_row_id,parent_path,prev_raw,curr_raw
```

Generic roles instead use value_1..value_N and raw_1..raw_N. Row IDs are one-based
among body rows. Parent paths join printed ancestor labels with ` > `. Nil and
header values are empty CSV fields; raw nil marks and printed negative zero are
preserved. Invalid values stay empty with raw retained and an invalid JSON status.

The JSON uses UTF-8, schema_version `1.0`, stable key order, ensure_ascii=False
and indent=2. Top-level fields are source (file basename/PDF page/backend), page
(title/correction/unit/multiplier/printed page), columns (index/role/cleaned
heading/ISO date), hierarchy_source, warnings and rows. Every tree node contains
row_id, label, row_type, level, values keyed by role (raw/value/status), and
children. Nil values are JSON null; header cells have empty status. There are
no timestamps or absolute paths. Generated samples use enforced LF line endings.

```bash
python -m pytest
python -m ruff check src/parser scripts tests/test_hierarchy.py tests/test_metadata.py tests/test_export.py
```

The report documents all 43 rows' GT agreement, byte invariance under six
coordinate transformations and a flat-indentation ablation. That ablation retains
row types/values but only 38 of 43 parent links, illustrating the partial fallback;
it is not a general accuracy claim. Evaluation metrics and robustness assessment
remain P7–P8 work.

## License

This project is a take-home assignment and is not licensed for redistribution.
