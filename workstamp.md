# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P9 |
| State | IN PROGRESS |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T10:03:00Z |

## Current prompt (verbatim)

P9: Independent review. You are a REVIEWER, not the builder. src/, tests/, eval/ and scripts/ were written by other agents (GPT-6.1 Sol in Codex; the setup and PDF inspection earlier by Claude Opus 4.6). You are read-only for source code: do NOT change anything in src/, tests/, eval/, scripts/ or data/. Allowed writes: notes/review_P9.md, notes/review_probes.py, workstamp.md, and one commit.

Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P9 IN PROGRESS, add a Sessions row with your actual model name, update workstamp.md after every step, and make small wip(P9) commits. If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure instead of starting over. Set PYTHONIOENCODING=utf-8 for all commands. Use the .venv.

## Budget discipline
My Opus quota is nearly used up. Be economical.
- Read fully ONLY: src/parser/{rows,classify,hierarchy,metadata,export,rules}.py, src/parser/evaluation/{alignment,metrics,accounting}.py, README.md, notes/{failure_analysis,evaluation_design,hierarchy_and_export}.md, workstamp.md. For tests, read file names and test names, and read test bodies only where a finding needs them.
- Do NOT open: eval/results/robustness_report.json, notes/words_*.json, notes/drawings.json, data/derived/*.
- Prefer commands and greps over reading whole files. No broad refactoring advice.

## Mission
Find real defects, weak spots and overclaims, with evidence. Trust nothing the builder claimed without verifying it by running something. Rank findings by severity (blocker / major / minor / nit).

## A. Verify the builder's claims by running things
1. Fresh-clone reproducibility: git clone the local repo into a temp directory, create a new venv, pip install -e ".[dev]", run pytest -q. Report the commands and the test count.
2. Determinism: regenerate the page-4 outputs (scripts/parse_page.py) and the evaluation (eval/run_eval.py) into a temp directory and diff them against examples/ and eval/results/. Report any difference.
3. Protected files: show with git diff --stat that P7-P8 (after commit 2f6fa06) did not change data/, data/raw/, or the production modules rows.py, classify.py, hierarchy.py, metadata.py, export.py, normalize.py, pdf_backend.py, layout_types.py.
4. GT-leak audit: grep the production code (src/parser outside evaluation/) for any reference to data/gt, "gt", "page4" or the GT file names. Confirm no production module reads GT, and that accounting.py takes no GT input and no label text.
5. Test-weakening audit: show git diff 2f6fa06..HEAD -- tests/ for the four existing test files modified in P7-P8 and state whether any assertion was removed or loosened.
6. Independent recomputation: in your own throwaway script (notes/review_probes.py), read the printed numbers with pdfplumber (reading the PDF is fine for a reviewer), recompute the subtotal, net and total residuals yourself, and compare with the accounting table in eval/results/page4_report.md. Also independently count rows (expect 43 body rows) and printed value cells.

## B. Targeted code review (look for these specific risks)
[...full prompt content...]

## C. Probes (at most 8, small and cheap)
[...full prompt content...]

## Deliverable: notes/review_P9.md
[...full prompt content...]

## Constraints and finish
Commit "P9: independent review"; set workstamp.md to DONE with "Next action: P10 apply review fixes"; append P9 to the Prompt history with the commit hash. Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P7-P8 IN PROGRESS, mark steps [~]/[x] as you go, and make small wip(P7-P8) commits (at least one per numbered section). If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure instead of starting over. If this is a new session (no memory of earlier chats): first run git status, git log -5 and the full test suite, report the real state, and add a Sessions row with your actual model name. Set PYTHONIOENCODING=utf-8 for all commands. Explain each design decision as you go.

## Goal
Define and measure "correct" for table extraction, as I promised in my email: (a) cell-level accuracy against hand-labeled ground truth, (b) structural accuracy (hierarchy and row/column alignment), (c) label-free accounting checks (subtotals, net rows, totals) with a rounding tolerance for 千円 units. Then stress the pipeline with perturbations and write an honest failure analysis. No new dependencies (stdlib and the installed packages only). Do not modify data/gt/, data/raw/ or the PDF. Never use GT inside the parser or inside the accounting checks.

## 1. Evaluator design rules
- The evaluator scores FILES, not internal objects: it reads a predicted flat CSV (schema from P6, utf-8-sig) and a GT CSV (data/gt/page4.csv), optionally the predicted JSON and data/gt/page4_meta.json. So any other system that writes the same CSV schema can be scored.
- Library in src/parser/evaluation/ (alignment.py, metrics.py, accounting.py, perturb.py, report.py or similar); run scripts in eval/ (eval/run_eval.py, eval/run_robustness.py). Deterministic: no timestamps, fixed seeds, stable ordering.
- The report must say what each metric means and its denominator.

## 2. Row alignment
Predicted and GT rows must be aligned before comparing, because a parser can drop, add or merge rows, and labels repeat (その他 appears three times, リース資産 twice, 減価償却累計額 four times). Implement an order-preserving sequence alignment (dynamic programming) with a similarity per pair: 0.5 x label similarity (1.0 if label_key equal, else a character-level ratio) + 0.5 x value similarity (fraction of value columns that are equal). A pair is aligned only if similarity >= a configurable threshold (default 0.5); gaps are free. Deterministic tie-breaking. Tests must prove that duplicates are aligned correctly when a row is missing or extra.

## 3. GT-based metrics (aligned rows)
- Cell accuracy: over all (GT row, value column) cells of aligned rows, exact match of the integer value; unaligned GT rows count as wrong. Nil (None) and 0 are DIFFERENT. Report two denominators: all cells (43 x 2) and printed-value cells only (cells whose GT raw string is not empty).
- Raw-string accuracy: exact match of prev_raw and curr_raw.
- Label accuracy: exact (as printed) and by label_key.
- Row-level: precision, recall, F1 of aligned rows, and the fraction of fully correct rows (label, both values, type, parent, level all correct).
- Structure: row_type accuracy plus a confusion matrix; level accuracy; parent accuracy, where a predicted parent is correct if it aligns to the GT parent (both root counts as correct; an unaligned parent is wrong), so duplicate labels cannot be confused; parent_path accuracy; mean ancestor-chain Jaccard against the GT chain, mapped through the alignment.
- Column assignment: if the JSON and meta are given, check column roles and period_end dates against the GT meta.
- Aggregation: a function that combines several page reports (micro-average of counts and a macro-average per page), tested by combining the same page twice. State in the report that with a single page the micro and macro averages coincide.

## 4. Label-free accounting checks (src/parser/evaluation/accounting.py)
Input: only the predicted rows (row_id, parent_row_id, row_type, value columns and their raw strings). No GT, no label text. Rebuild the tree from parent_row_id.
- contribution(node): if the node has a child of type net, the net child's value; else if the node has values, its own value; else (a header) the value of its subtotal child, or not evaluable if it has none.
- Sum check for every subtotal and total row S: the expected value is the sum of contribution(c) over the siblings that precede S under the same parent. (Example in plain words: a tangible-assets subtotal adds the net rows and the lines that have no net row, not the gross or accumulated-depreciation rows; the fixed-assets subtotal adds the subtotals of its sub-sections; total assets adds current-assets and fixed-assets subtotals.)
- Net check for every net row N under gross item G: expected = G value + the contra child value (contra values are printed negative).
- Balance identity: if exactly two rows have type total, check that they agree; otherwise status not_applicable (on page 4 there is only one).
- Nil handling: a None value counts as 0 in a sum only if its raw string is a nil marker; a None from an invalid or unparseable raw makes the check not_evaluable.
- Each check outputs: check id, kind, row_id, value column, number of addends n, expected, printed, residual (printed minus expected), tolerance, status in {exact, within_tolerance, fail, not_evaluable, not_applicable}.
- Tolerance policy (document the derivation in notes/evaluation_design.md): figures are rounded or truncated to the printed unit individually, so printed sums need not match exactly. Default tolerance = n (the number of addends, at least 1); this covers both per-figure truncation and per-figure rounding to nearest. Make the tolerance function replaceable (a ToleranceModel).
- Extra diagnostic, reported but NOT used for pass/fail: truncation consistency. If every printed figure is truncated toward zero, a residual must lie in the integer interval [-(number of negative addends), (number of positive addends) - 1]. Report for each check whether it lies inside, and the fraction of checks that do. Present this as a hypothesis (Japanese filings commonly truncate each figure) that I verify, not as a fact. My hand-check of page 4 found residuals between -1 and +3 thousand yen; check my claim and report what you actually find.
- Summary: counts per status and an accounting pass rate = (exact + within_tolerance) / evaluable checks.

## 5. Reports
- eval/run_eval.py --pred CSV [--pred-json JSON] --gt CSV [--gt-meta JSON] [--out-dir DIR] writes eval/results/page4_report.json and page4_report.md: metric tables with denominators, the confusion matrix, every mismatch listed with row_id, label and field, the full accounting check table, and a "Limitations of this evaluation" section stating honestly: single page; the parser rules were designed after seeing this page, so these numbers are a development result and NOT a generalisation claim; the GT was drafted by an AI agent and verified by one human; the truncation hypothesis rests on one page.
- Commit the results.

## 6. Perturbation framework (src/parser/evaluation/perturb.py, eval/run_robustness.py)
Perturb the RawPage (read the PDF once with the P4 backend), never the PDF. Reuse or move the helpers that the P4/P5-P6 tests already use (translate, scale, shuffle, jitter), keep all existing tests passing, and add: flatten_indentation (each row's label tokens moved to the same x0), drop_rules (remove all rule rectangles), and separate x-jitter and y-jitter. For each perturbed page, run the full pipeline and the evaluator.
a) Geometry sweep: jitter amplitude in units of the median word height, 0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, separately for the y axis and the x axis, 20 seeds (0..19) each; per amplitude report the mean and the worst case of cell accuracy, row F1, parent accuracy and accounting pass rate, and the number of crashes. Find and state where it breaks and which threshold in the layout config is responsible.
b) Structural ablations: flattened indentation; dropped rules; translate; scale (two factors); shuffled word order. Report the full metric set for each.
c) Fault injection on the PARSED values (label-free detector quality, no GT needed for detection): for every printed numeric cell, exhaustively (no randomness): every single-digit substitution (each digit position, each different digit, skipping substitutions that create a leading zero), a sign flip, and blanking the cell to nil. Re-run the accounting checks and record whether at least one check that passed before now fails ("detected"). Report: the fraction of cells that take part in at least one check (coverage); the detection rate by fault type; for digit substitutions the detection rate by digit position (units digit versus higher digits); and which undetected faults hide inside the tolerance (state the number of addends involved). Explain in plain words that a last-digit error in a sum with many addends can slip under the tolerance.
Everything deterministic. Keep the sweep runtime reasonable (well under a couple of minutes); if it is not, reduce the seeds and say so.

## 7. Failure analysis (notes/failure_analysis.md)
Based only on the experiments you actually ran: a table of failure modes (what breaks, the trigger, how it shows up in the metrics and in the accounting checks, which rows are affected with examples, the root cause in the code or the rules, and a recommended next step), including the flattened-indentation errors found earlier (3 sub-section headers, the fixed-assets subtotal, the allowance contra row). Separate "observed in experiments" from "expected but not tested" (scanned pages, tables spanning pages, wrapped labels, multiple tables, other statements, other languages). Do not claim robustness that you did not measure.

## 8. Tests (the evaluator must itself be tested)
- Synthetic cases: perfect prediction gives 1.0 everywhere; one wrong cell; swapped columns; None versus 0; a missing row; an extra row; duplicate labels with one missing; wrong parent; wrong type; label OCR-style typo with correct values (still aligned); empty prediction; empty GT.
- Accounting: synthetic trees with nested header and subtotal, net rows, nil handling, an invalid cell (not_evaluable), tolerance boundary (residual exactly n and n+1), truncation-interval boundaries, balance identity with two totals and with one, a header without a subtotal child.
- Real page: the parser output scored against GT must give 1.0 on all GT metrics (as P5-P6 showed), and the accounting checks must all be exact or within tolerance (report the numbers, including the truncation-consistency fraction).
- Perturbation helpers are deterministic (same seed, same output); fault injection is deterministic and covers the cells you expect (assert on counts you computed from the data, not hard-coded financial values).
- Evaluator CLI works without PYTHONIOENCODING set. Run the full suite and ruff.

## 9. Docs
Update README (how to run evaluation and robustness). Write notes/evaluation_design.md: what "correct" means here, every metric with formula and denominator, the alignment algorithm, the accounting rules, the tolerance derivation and the truncation hypothesis, the perturbation and fault-injection design, and the limitations. Keep it readable: it feeds my write-up.

## Constraints
- Do not weaken a test to make it pass. If an experiment exposes a real parser bug, do NOT fix it silently in this prompt: record it in notes/failure_analysis.md with evidence (a later prompt applies fixes after an independent review), unless it is a crash in the new evaluation code itself.
- Final commit "P7-P8: evaluation framework, robustness experiments, failure analysis"; set workstamp.md to DONE with "Next action: independent review (P9)"; append P7-P8 to the Prompt history with the commit hash.

## Final message must show
Orientation (repo state, test count before this prompt); the public API and the CLI commands; the GT metric table for the real page; the accounting check table (n, expected, printed, residual, status) and the truncation-consistency fraction; the geometry sweep summary (where it breaks); the ablation table; the fault-injection results (coverage, detection by fault type and digit position); the top failure modes; test and ruff output; files created or modified; commit hashes; known limitations; open questions.

## Plan for this prompt

1. [x] Orient, baseline tests/fingerprints; define independent file schema and evaluator contracts; commit section 1.
2. [x] Implement deterministic ordered alignment with duplicate/gap cases; commit section 2.
3. [x] Implement metrics, mismatch records and aggregation with denominators; commit section 3.
4. [x] Implement label-free accounting, replaceable tolerance and truncation diagnostics; commit section 4.
5. [x] Generate JSON/Markdown reports and evaluator CLI; commit section 5.
6. [x] Implement deterministic perturbations, geometry/ablation sweeps and exhaustive fault injection; run and commit section 6.
7. [x] Document observed failure analysis, separated from untested expectations; commit section 7.
8. [x] Test evaluator/accounting/perturbations/faults/CLI against synthetic and real files; commit section 8.
9. [x] Document formulas, accounting derivation, designs, limitations and README commands; commit section 9.
10. [x] Full suite then ruff, final integrity checks, completion commit and DONE handoff.

## Files created or modified

- src/parser/evaluation/__init__.py — evaluator package.
- src/parser/evaluation/data.py — independent CSV records and schema reader.
- src/parser/evaluation/alignment.py — deterministic ordered dynamic programming.
- src/parser/evaluation/metrics.py — GT metrics, mismatches and aggregation.
- src/parser/evaluation/accounting.py — label-free checks and tolerance model.
- src/parser/evaluation/report.py — file API and deterministic JSON/Markdown reports.
- src/parser/evaluation/perturb.py — shared geometry and ablation helpers.
- src/parser/evaluation/faults.py — exhaustive numeric fault experiments.
- src/parser/evaluation/robustness.py — file-scored sweeps and ablations.
- eval/run_eval.py; eval/run_robustness.py — UTF-8 command-line entry points.
- eval/results/page4_report.json; eval/results/page4_report.md — real-page results.
- eval/results/robustness_report.json; eval/results/robustness_report.md — full deterministic experiments.
- tests/test_evaluation.py; tests/test_accounting.py; tests/test_perturbation.py — 52 new tests.
- tests/test_rows.py; tests/test_export.py — reuse moved helpers, assertions preserved.
- tests/test_inspection.py; tests/test_smoke.py — legacy import/format cleanup for full-tree ruff, assertions preserved.
- notes/evaluation_design.md — formulas, accounting derivation, designs and limitations.
- notes/failure_analysis.md — measured failures versus untested expectations.
- README.md — API, commands and results; .gitattributes — report LF policy.
- workstamp.md — verbatim request, plan, results, boundaries and handoff.

## Last action and result

P7-P8 complete. Final implementation commit f3dcc47251642cb368bf5f69aab3c82df7ae9534.
Sections 1–9 committed; all requested real-page reports,
360 sweeps, six ablations and 3,817 faults recorded. Final tests/lint/integrity
checks pass. No existing parser behavior changed. P9 has not started.

Full suite: 275 passed in 8.73s (baseline 223). Full-tree ruff check src scripts
tests eval: All checks passed! Scoped formatting applied; no assertion weakened.
19 protected-file hashes match baseline (all GT/raw/examples/original parser
modules/dependency manifests); GT CSV still UTF-8 BOM. Verbatim request matches
attachment exactly. Reports regenerated after evaluator fixes and artifact test passes.

Section 9 documents every metric/denominator and accounting derivation, including
the literal truncation interval's negative-only/zero edge cases. README includes
public API and reproducible commands; report LF attributes added.

52 new evaluator/accounting/perturbation tests pass in 2.76s. Tests exposed two
new-evaluator issues: role presence was insufficient to score column assignment;
JSON report dependencies needed list normalization. Both fixed in evaluation code,
not parser code; tests preserved. Reports and all 360 sweeps regenerated. Added
missing-role reasons, pooled accounting aggregation and explicit fault participation.

Failure analysis written from measured seed/ablation/fault outputs, separating
observed failures from untested expectations. No parser code fixed. Documents
check disappearance/undefined rates, flat-parent errors and tolerance blind spots.
Section 6 commit 6c3694b.

Section 6 full experiment ran: 360 sweeps, all 20 seeds retained, no crashes.
First tested degradation y=0.2H, x=0.3H. All six ablations completed. Numeric
coverage 72/72; faults=3817; digit detection3256/3673, sign71/72, nil71/72.
Units digit249/648; higher3007/3025. Helpers moved from tests, unchanged
existing assertions; 35 helper/integration tests passed (3 CLI deselected here).

Real-file JSON/Markdown reports generated: GT metrics perfect; accounting
7 exact +13 within tolerance, 2 balance N/A; 20/20 truncation intervals agree.
Residuals observed -1 to +3, confirming supplied page-specific hand-check range.

Label-free accounting smoke run completed; all evaluable real-page checks
pass default n-addend tolerance. Exact counts/residuals printed for report.
Accounting records contain no labels or GT reference.

Section 3 real-file metric smoke check: every GT metric scores 1; mismatches
empty; duplicate-page micro aggregation passes. Counts/denominators are explicit.

Section 2 alignment smoke checks pass: full real-page alignment; dropped
duplicate-label row correctly left unmatched. Similarity uses labels/values only.
Section 1 commit 464b2cc.

Baseline: 223 passed in 8.72s. All GT/raw/examples/parser files fingerprinted.
Independent exported-file reader smoke check passes: 43 rows, two named value
roles, no input issues; GT parent IDs derived from paths, prediction IDs explicit.

Read brief/handoff; tree clean at 7bc7084. P5-P6 DONE; prior suite 223 passed.
Existing Session 5 continues; no new session row and no interrupted work found.

## Decisions and assumptions

- Evaluator consumes exported files and independent CSV records, never ParsedPage for scoring.
- Accounting receives only IDs, types and amount/raw columns: labels/GT excluded by data model.
- GT/raw/PDF and existing parser behavior remain unchanged. Exposed parser failures are documented, not fixed here.
- Fixed seeds, deterministic report ordering, no timestamps. Use PYTHONIOENCODING=utf-8.

## Known issues / open questions

Measured limitations: y row clustering breaks from tested 0.2H; x column/indent
clustering from 0.3H; flat fallback loses five parent links. Accounting check
disappearance and n-addend tolerance can mask errors. See failure_analysis.md.
Open questions: human confirmation of filing truncation policy; negative-only
edge cases in the requested diagnostic interval; held-out documents and ambiguous
identical GT paths. Pytest fixtures need unsandboxed temp access in this environment.

## Next action

independent review (P9)

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | Image-derived GT, 43 rows; now VERIFIED by human with no corrections; 12 tests pass | 0be2cf6 (initial GT); verification: 9805d79 |
| P3 | Pure normalization utilities, 129 new tests; full suite 141 passed; GT unchanged | b41840c |
| P4 | Pure relative row/column/indent reconstruction, GT matched; 166 tests pass | 2582b5d |
| P5-P6 | Typed rows, parent tree, metadata and deterministic exports; 223 tests pass; GT unchanged | 2f6fa06 |
| P7-P8 | Independent file evaluator, label-free accounting, deterministic robustness/fault experiments, failure analysis; 275 tests pass; protected files unchanged | f3dcc47251642cb368bf5f69aab3c82df7ae9534 |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
