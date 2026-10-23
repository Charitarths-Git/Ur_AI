# jp-balance-sheet-parser

Parse Japanese consolidated balance sheets (連結貸借対照表) from PDF into structured CSV and JSON.

> **Status**: P13 reproduction checks passed on Windows / Python 3.14.0; hygiene review remains. GT is **VERIFIED**.
> Next action: final export_chat.py, redaction of chat_logs, add the Claude conversation log, submit.

## Results at a glance

See [REPORT.md](REPORT.md) for the draft write-up, correctness definitions,
measured results, remaining failures and facts awaiting human confirmation.

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

# Set UTF-8 console I/O (PowerShell; cmd uses set PYTHONIOENCODING=utf-8)
$env:PYTHONIOENCODING="utf-8"

# 3. Choose ONE install route: pinned dependencies for scripts/tests
pip install -r requirements.lock

# 3b. Or install the local package with flexible dependencies (editable, for development/API use)
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
│       ├── export.py      # Parsed-page pipeline and deterministic CSV/JSON (P6)
│       └── evaluation/    # Independent file metrics, accounting and experiments (P7–P8)
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
├── eval/                  # Evaluation CLIs and committed deterministic results
├── notes/                 # Inspection findings and design notes
├── PROJECT_BRIEF.md       # Full task description and plan
├── workstamp.md           # Session handoff state (read this first!)
├── pyproject.toml         # Python project metadata and deps
└── requirements.lock      # Pinned dependency versions (pip freeze)
```

## Phases

PROJECT_BRIEF.md retains the original plan; workstamp.md is the current handoff
record. P10b was an additional audit after P10. The write-up remains a draft for
human editing, and P12 is optional.

| Phase | Scope |
|---|---|
| P0 — Setup | Repository layout, dependencies, smoke test ✅ |
| P1 — Inspect the PDF | Diagnostic extraction; understand text layer and layout ✅ |
| P2 — Ground truth | Image-derived GT verified by human, no corrections ✅ |
| P3 — Normalization | Pure amount, label-matching and period helpers with tests ✅ |
| P4 — Row reconstruction | Relative row/column reconstruction, visual indent steps and rule evidence ✅ |
| P5 — Hierarchy inference | Typed rows, parent paths, metadata and partial fallback ✅ |
| P6 — CSV and JSON export | Deterministic flat CSV and hierarchical JSON; committed examples ✅ |
| P7 — Evaluation metrics | Independent file metrics, alignment and label-free accounting ✅ |
| P8 — End-to-end run | 360 geometry sweeps, six ablations, exhaustive faults and failure analysis ✅ |
| P9 — Independent review | Review by a different AI agent ✅ |
| P10 — Review fixes | Apply fixes from the review ✅ |
| P10b — Audit | Audit fixes, close reporting/test gaps; remaining geometry limits documented ✅ |
| P11 — Write-up | Draft complete; human rewrite remains ✅ |
| P12 — OCR/VLM stub | Optional backend stub for scanned pages |
| P13 — Reproducibility | Both fresh install routes, tests and artifact comparisons verified ✅ |

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
otherwise columns use value_1..value_N and warn. No supported value columns
emits no_columns_detected; one emits one_column_detected. No reconstructed body
emits no_body_rows and hierarchy empty_input. JSON and CLI list these warnings. Unit multipliers are metadata
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
it is not a general accuracy claim. The P7–P8 evaluation below measures these limitations explicitly.

## Evaluation and robustness (P7–P8)

With the virtual environment active, run from the repository root:

```bash
python eval/run_eval.py --pred examples/balance_sheet_after_correction_p1.csv --pred-json examples/balance_sheet_after_correction_p1.json --gt data/gt/page4.csv --gt-meta data/gt/page4_meta.json
python eval/run_robustness.py
```

Both CLIs configure UTF-8 console output automatically. The evaluator accepts any
prediction using the P6 flat CSV schema (`utf-8-sig`); JSON/meta inputs are optional
and enable column-role/date checks. `--threshold` controls the default 0.5 ordered
alignment threshold; `--out-dir` changes the report directory. Reports are
[page4_report.md](eval/results/page4_report.md) and its adjacent JSON, with every
metric numerator/denominator, mismatch, confusion matrix and accounting check.

The public file API is:

```python
from parser.evaluation.report import evaluate_files, write_report
from parser.evaluation.metrics import aggregate_reports

report = evaluate_files(pred_csv, gt_csv, pred_json=pred_json, gt_meta=gt_meta)
write_report(report, out_dir)
combined = aggregate_reports([report, report])  # pooled counts + per-page means
```

Scoring reads files independently of parser internals. Order-preserving dynamic
programming aligns rows using label/value similarity, including repeated labels.
Missing GT rows count as wrong; extra predicted rows reduce row precision. Nil
and integer zero are different. Empty metric denominators are undefined, not
perfect. With one page the micro/macro averages coincide. `accounting_checks`
accepts only `AccountRow` IDs, types, values and raw amounts: no labels or GT.
Its replaceable tolerance defaults to the number of addends (at least one).
Without a net child, gross contribution includes contra children; unknown
negative labels remain line_item with possible_contra_or_loss.

The real page scores 1.0 on every GT metric (86/86 cells, 43/43 rows). Accounting
has 7 exact and 13 within-tolerance checks, no failures, and two balance checks
not applicable. Residuals range from -1 to +3 千円. All 20 evaluable checks fit
the requested truncation interval, a diagnostic hypothesis that still needs
human confirmation of the filing's policy. `evaluable_fraction` is evaluable /
applicable accounting checks (excluding not_applicable). Pass rate is N/A with
no evaluable checks. JSON/Markdown headlines show both; robustness geometry
tables show mean/minimum over defined seeds, and ablations show both values.

The robustness CLI reads the PDF once, perturbs RawPage geometry, then runs the
full parser/export/file-evaluation pipeline. It retains all 20 seeds (0..19) for
nine amplitudes on each axis: 360 runs, well under two minutes locally. It also
runs six structural/geometry ablations and 3,817 exhaustive value faults. Results
are committed in [robustness_report.md](eval/results/robustness_report.md) and its
adjacent JSON. First measured degradation is at y-jitter 0.2 word heights and
x-jitter 0.3; flattened indentation preserves values but damages parent structure.
All 72 numeric cells participate in accounting checks, yet only 249/648 units-digit
faults are detected because small changes can hide inside a many-addend tolerance.

These are **development results on one page**, whose rules were designed after
seeing it. They do not establish generalisation. The AI-drafted GT was verified
by one human, who also reported an independent second review. Accounting pass
rates must be read alongside not-evaluable counts: severe geometry damage can
remove checks without producing failures. P10 fixes have now had an audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit (P10b). Remaining geometry
limitations are recorded with current measurements.

See [evaluation_design.md](notes/evaluation_design.md) for formulas, denominator
rules, accounting derivation and experiment design, and
[failure_analysis.md](notes/failure_analysis.md) for measured failures and untested
expectations. Run all tests and lint with:

```bash
python -m pytest
python -m ruff check src scripts tests eval
```

## P10b audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit

The audited starting state was283 tests at e40462b, including the seed11 failure
regression from7f5afbd. [p10_audit.md](notes/p10_audit.md) records initial/final
status per requirement. [failure_analysis.md](notes/failure_analysis.md) preserves
the P8 baseline and adds all P8/P10/current geometry, ablation and fault tables.

Gap clustering improved P8 x=.3H mean cell accuracy0.3331 to0.9360 and y=.3H
0.5994 to0.8890. P10b does not change these scores. All20 x=.3 seeds detect two
correct column roles; the remaining errors come mostly from the cell-assignment
gate. The seed11 y=.2 split remains. A pitch-based candidate was rejected at its
first existing-test failure; no threshold change was retained. A high accounting
pass rate can coexist with low evaluable_fraction, so read both columns.

## Clean-clone reproduction (P13)

[notes/p13_clean_clone_check.md](notes/p13_clean_clone_check.md) records the tested
commit, commands, hashes and masked hygiene findings. Both Quick start install
routes passed in separate fresh environments on Windows / Python 3.14.0. This
checks that environment; other Python versions and operating systems were not
newly tested. The pinned route installs dependencies for the repository scripts
and tests; the editable route also installs the local package for API use.

After activating the environment, these commands reproduce the committed results:

```bash
python -m pytest
python -m ruff check src scripts tests eval
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf --page 1 --out-dir outputs
python eval/run_eval.py --pred examples/balance_sheet_after_correction_p1.csv --pred-json examples/balance_sheet_after_correction_p1.json --gt data/gt/page4.csv --gt-meta data/gt/page4_meta.json
python eval/run_robustness.py
```

The evaluator command scores the committed example files. The check first
compared freshly generated outputs with those examples byte for byte, then
compared all four regenerated evaluation reports with their committed versions.
Only the temporary clones were used to regenerate reports during the check.
Tracked conversation logs still need the final human export/redaction review;
a reproducible result does not mean the repository is ready for public release.

## License

This project is a take-home assignment and is not licensed for redistribution.
