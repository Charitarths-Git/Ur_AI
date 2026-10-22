# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P4 |
| State | DONE |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-22T22:23:56Z |

## Current prompt (verbatim)

P4: Row reconstruction and indent clustering. Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P4 IN PROGRESS, mark steps [~]/[x] as you go, and make small wip(P4) commits. If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure instead of starting over. If this is a new session (you have no memory of earlier chats): first run git status, git log -5 and the full test suite, report the real state, and add a Sessions row with your actual model name. Set PYTHONIOENCODING=utf-8 for all commands. Explain each design decision as you go.

## Goal
Turn the words and drawings of a PDF page into clean visual rows, separating label text from the value columns, plus raw layout evidence for later phases. Hard scope limits: NO hierarchy (no parent, no level), NO row_type, NO accounting words or label rules (that is P5), NO CSV/JSON export (P6), NO evaluation module (P7). Use parse_amount, label_key and parse_period_end from src/parser/normalize.py (P3); change that file only to fix a real bug, and report it if you do.

## Design requirements
1. Separate the PDF backend from the logic. Only one module (src/parser/pdf_backend.py) may import pymupdf. It returns a plain RawPage: page width/height, a list of Word (text, x0, y0, x1, y1, size or None), and a list of Rule (thin horizontal drawn rectangles or line segments with coordinates; also keep their height). Define the backend as a small interface so an OCR or VLM backend can be added later (do not implement one).
2. All reconstruction logic is PURE functions on RawPage, so it can be tested without a PDF: reconstruct_page(raw_page, config) -> PageLayout. It must depend only on RELATIVE geometry: every threshold is a multiple of the median word height (or a fraction of the page size), collected in a documented LayoutConfig dataclass. No hard-coded point coordinates, no page-4-specific numbers (no row counts, no y limits like "skip y < 145"). A later phase will perturb word lists (shift, scale, jitter, shuffle) and re-run this, and your tests below check this property.
3. Output structures (frozen dataclasses; names may vary if you justify them):
   - Column: index, x1 centre, heading text, period_end (from parse_period_end, or None).
   - Cell: column index, raw string exactly as printed, AmountResult from parse_amount.
   - Row: index, zone ("header", "body", "footer"), y top/bottom, label (as printed, see 5), label_x0, indent_step (body rows with a label, else None), cells, rule_above (bool), source words.
   - PageLayout: rows, columns, indent step centres, the thresholds actually used.

## Algorithm guidance (you may improve it; document your choices)
1. Row clustering: sort words by vertical centre (PyMuPDF returns stream order, not visual order; the footer comes first), group words whose centre is within a tolerance of the group, sort each row by x0. Tolerance = factor x median word height. Report the value used on the real page.
2. Value columns: candidate tokens are those parse_amount accepts as "ok" or "nil". A token is a VALUE only if its RIGHT edge lines up with a detected column; a parseable token elsewhere (a digit inside a title, the page number, a date) is not. Detect columns by clustering the right edges (x1) of candidates, with a minimum number of supporting rows (configurable), robust to stray tokens. Numbers are right-aligned and nil dashes share the same right edge. A numeric token with an invalid status that sits in a column is kept as a cell (status "invalid"), never dropped.
3. Fused or split signs: the text layer fuses the minus marker with digits ("△2,979"). Also handle a lone sign token directly left of its digits by merging them (tested with synthetic words).
4. Zones, structurally and not by coordinates: the header zone ends after the last row containing a period heading (parse_period_end finds a date) or, failing that, the last row above the first row with a value cell; document the fallback. The footer is every row after the last row with a value cell. State these limitations in the notes (e.g. a page that ends with a label-only row).
5. Labels: label = body row tokens that are not values, joined in x order, inserting a space only where the gap is larger than a configurable fraction of the word height. Labels must be exactly as printed (no normalization). Report how many labels contain internal spaces.
6. Column headings: for each column, collect the header-zone text above it; set period_end per column. Do not hard-code "previous" or "current"; leave the mapping to a later phase.
7. Indent clustering: take the label_x0 of body rows, cluster them in 1D (gap-based, tolerance relative to word height) and assign indent_step 0..k-1 from left to right, keeping the raw x0 too. Do NOT turn indent steps into levels or parents.
8. Rule evidence: rule_above is True when a thin horizontal Rule lies between the previous row and this row and overlaps a value column horizontally. Wide shaded backgrounds are not rules (use the Rule height limit as a config value). This is evidence only; do not interpret it.
9. Add scripts/dump_rows.py PDF_PATH [--page N]: prints zone, y, indent_step, label, raw cells, rule_above for every row, plus the columns and thresholds. It must work WITHOUT PYTHONIOENCODING set (reconfigure stdout and stderr to UTF-8 at start). Apply the same fix to scripts/inspect_pdf.py and the other scripts.

## Tests
- tests/test_rows.py with SYNTHETIC RawPage inputs (no PDF): jittered y values; shuffled word order (footer first); a label that contains a digit but is not right-aligned (must stay in the label); fused and split signs; nil tokens; invalid tokens in a column; a page with no body; empty input; a page with three value columns; different font sizes.
- Invariance tests on a synthetic page and on the real page: shuffling the words, translating all coordinates by (dx, dy), and scaling all coordinates by a factor must give the same labels, cells, zones and indent steps. Small coordinate jitter (below your tolerance) must also leave results unchanged.
- Integration test on data/raw/balance_sheet_after_correction.pdf compared READ-ONLY with data/gt/page4.csv and data/gt/page4_meta.json (utf-8-sig): body row count equals the GT row count; for every row in order, label_key equals the GT label_key, the raw strings equal GT prev_raw and curr_raw exactly (header rows have no cells), and parsed values equal the GT values; the number of columns equals 2; each column's period_end equals parse_period_end of the matching period heading in the meta file. Report (do not assert) how many labels match GT exactly, not only by label_key.
- Informational report, not an assertion: a cross-tab of rule_above against the GT row_type, and the indent_step against the GT level. Put it in notes/row_reconstruction.md. Use the GT ONLY in tests and this report, never inside the algorithm.
- A subprocess test that runs scripts/dump_rows.py and scripts/inspect_pdf.py with PYTHONIOENCODING and PYTHONUTF8 removed from the environment and checks that they exit successfully.
- Run the complete suite, then ruff.

## Docs
Update README (new modules, how to run dump_rows.py). Write notes/row_reconstruction.md: the algorithm, every threshold with its default and why, the observed values on the real page, the cross-tab report, and a "Known limitations" list (wrapped labels, multi-line headings, tables spanning pages, label-only last rows, sub-column headings, rotated or scanned pages, multiple tables on one page).

## Constraints
- Do not modify data/gt/, data/raw/ or the PDF. Dependencies: stdlib and the already installed pymupdf only. Do not weaken a test to make it pass; if the GT comparison fails, report it and investigate the algorithm. Do not edit the GT.
- Final commit "P4: row reconstruction and indent clustering"; set workstamp.md to DONE with "Next action: P5 hierarchy and parent paths"; append P4 to the Prompt history with the commit hash.

## Final message must show
Orientation (repo state, test count before P4); the public API; the thresholds used and the values observed on the real page (row tolerance, column x1 centres, indent step centres, number of rows per zone); the GT comparison result; the rule_above and indent cross-tab; test and ruff output; invariance test results; files created or modified; commit hashes; known limitations; open questions.

## Plan for this prompt

1. [x] Orient: baseline suite, protected-data fingerprints, inspect existing code and diagnostic formats.
2. [x] Define frozen layout structures/config and PDF backend interface; implement extraction adapter.
3. [x] Implement pure relative-geometry reconstruction; inspect actual layout and resolve issues.
4. [x] Add dump_rows CLI and UTF-8 startup to existing scripts.
5. [x] Add synthetic, invariance, GT integration and no-encoding subprocess tests; investigate failures.
6. [x] Document algorithm/thresholds/observations/cross-tabs/limitations and README usage.
7. [x] Run full suite then ruff, verify protected data unchanged, finalize P4 commit and handoff.

## Files created or modified

- src/parser/layout_types.py — frozen backend-neutral records, relative config and actual thresholds.
- src/parser/pdf_backend.py — PageBackend protocol and PyMuPDF adapter for words/thin rules.
- src/parser/rows.py — pure rows/columns/zones/indent/rule reconstruction.
- scripts/dump_rows.py — one-based page CLI, text diagnostics only.
- scripts/_console.py — shared UTF-8 stdout/stderr startup.
- scripts/inspect_pdf.py, gt_selfcheck.py, gt_crosscheck.py, render_gt_crops.py,
  export_chat.py — UTF-8 startup and lint/format cleanup; no diagnostic behavior changes.
- tests/test_rows.py — 25 synthetic, invariance, integration and CLI tests.
- notes/row_reconstruction.md — algorithm, thresholds, real-page evidence, GT cross-tabs and limitations.
- README.md — P4 modules/API/CLI and P5 next phase.
- workstamp.md — P4 prompt, plan, progress and completion evidence.

## Last action and result

Orientation: clean tree at 6374dbf; baseline 141 passed in 9.91s.
P4 targeted suite: 25 passed in 6.19s. Final full suite: 166 passed in 6.86s.
Then ruff on all new package modules, all scripts and test_rows.py: All checks passed!
Twelve invariance cases pass on both synthetic and real pages: shuffle, translation,
scales 0.45/2.75, combined transform and bounded jitter. Both no-encoding CLI
subprocesses pass with -X utf8=0. Full evidence is in notes/row_reconstruction.md.

Observed H=8.963989, row tolerance=3.137396; value x1 centres=397.513123/522.553162.
Indent centres=62.280000/75.239998/88.199997/101.279999/114.239998.
Zones=6 header,43 body,1 footer. GT: all 43 rows and 74 printed cells match;
43/43 labels match exactly, 0 labels with internal spaces. No GT failure/correction.
Rule and indent cross-tabs are informational only and recorded in the report.

Every GT/raw file SHA-256 equals its pre-P4 value. CSV remains UTF-8 BOM, hash
c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835.
P3 normalize.py and dependency manifests unchanged. Verbatim P4 prompt exact.

Progress commits: 5785b3f plan/baseline; d34449f backend/types; 85698fe pure logic;
265e765 CLI/encoding/rule span overlap; bd9022b tests; 1d24b2a docs/report/style.
Final P4 commit succeeded:
2582b5d96fa7950b23c1dd5a9ce2c9fda181b4dc — P4: row reconstruction and indent clustering.
This metadata-only follow-up records the hash and DONE status, following P3.

## Decisions and assumptions

- Existing Session 5 continues; no session row added. PYTHONIOENCODING=utf-8 used.
- Frozen layout records use tuples; raw input is never mutated. Only the package
  pdf_backend imports pymupdf; legacy P1/P2 diagnostic scripts retain their imports.
- Geometry uses H-relative configurable distances and a relative empty-input fallback.
  Column support counts distinct rows. All actual thresholds are exposed in PageLayout.
- P3 parsing/key/date helpers are reused; P3 normalization needed no changes.
- Date rows end header; no-date fallback starts at first supported valid value row.
  Last aligned cell ends body; invalid aligned values are retained, not dropped.
- Headings are collected by geometric bands without previous/current assumptions;
  units may be included. Labels retain original text with gap-based spacing.
- Visual indent steps and thin-rule overlap are evidence only: no hierarchy,
  semantic row types, accounting rules, exports or evaluation module implemented.
- GT is used only in integration tests and the informational report, never algorithm code.
- Shared UTF-8 CLI startup fixes Windows output. Lint formatting and removal of two
  unused legacy exporter locals do not alter existing diagnostic/export behavior.

## Known issues / open questions

No unresolved P4 failures or open design questions. Known limitations are documented:
wrapped labels; split/multi-line and sub-column headings; page-spanning/multiple
tables; label-only boundary rows; repeated aligned label digits; very short/all-invalid
columns; noise crossing decision boundaries. Rotated pages are rejected; scanned
pages require a future backend. Rule flags are visual evidence, not financial roles.
Configured upstream origin/main is gone; no remote operations requested.

## Next action

P5 hierarchy and parent paths

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | Image-derived GT, 43 rows; now VERIFIED by human with no corrections; 12 tests pass | 0be2cf6 (initial GT); verification: 9805d79 |
| P3 | Pure normalization utilities, 129 new tests; full suite 141 passed; GT unchanged | b41840c |
| P4 | Pure relative row/column/indent reconstruction, GT matched; 166 tests pass | 2582b5d |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
