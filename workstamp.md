# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P10b |
| State | DONE |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T11:15:12Z |

## Current prompt (verbatim)

P10b: Audit the P10 fixes and close the small gaps. Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P10b IN PROGRESS, mark steps [~]/[x] as you go, and make small commits ("fix(P10b): ...", "test(P10b): ...", "docs(P10b): ..."). If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure. If this is a new session: first run git status, git log -8 and the full test suite, report the real state, and add a Sessions row with your actual model name. Set PYTHONIOENCODING=utf-8. Explain decisions as you go.

## Context
The fixes from the independent review (notes/review_P9.md) were NOT applied by you: they were applied in a different tool and session (commits 5565491 and d51c47f, tests 275 -> 282), by the same agent that wrote the review. You are now the independent auditor, and you built the original code. Do not redo the fixes. Verify them. Do not modify data/gt/, data/raw/ or the PDF. Do not weaken or delete any test. Do not tune any threshold to page-4 numbers.

## A. Audit table (first, before any change)
For each requirement below, report PASS / PARTIAL / MISSING with evidence (file:line, a test name, or command output). Put the table in notes/p10_audit.md.
1. eval/results/baseline_P8/ holds the P8 results and was committed BEFORE the code changes (check git history order).
2. F2: contribution = net child, else own value plus contra children values; tests for gross+contra with no net row, with a net row, nil and invalid cases, nested case; page-4 accounting still 20/20 with the same residuals.
3. F1: no structural contra classification; a non-listed label with all-negative cells gives line_item plus the warning code possible_contra_or_loss (on the row and the page); page 4 has 5 contra rows by label rule and ZERO warnings; notes/hierarchy_and_export.md updated.
4. F3: evaluable_fraction in accounting_summary(); pass rate N/A when nothing is evaluable; both shown in the headline of the markdown and JSON reports AND in every robustness table (mean and minimum over seeds); tests for the zero-evaluable and the mixed case.
5. F4+F5: one shared gap-based clustering helper used for rows, value-column right edges and (if applicable) indent steps; a synthetic test with row pitch about 1.3 word heights plus jitter; regression tests recreating the two measured failures (x-jitter 0.3 H seed 1: two columns with correct roles; y-jitter 0.2 H seed 11: the lease accumulated-depreciation row stays intact); all invariance tests pass; examples/ byte-identical to before P10.
6. F7+F9: no_columns_detected warning, one-column warning, a correct empty-input hierarchy warning; tests for a one-column page, an empty page and a page with no body.
7. Fault-injection oracle test: a hand-written tree (about four addends, a subtotal and one net row) with a brute-force detector written INSIDE the test, compared with the library's counts; plus an assertion that the number of injected digit faults on the real page equals the number derived from the digit counts of the printed numeric cells.
8. F8: structured issues from read_table.
9. Docs: README, notes/evaluation_design.md and notes/failure_analysis.md updated with a before/after table (baseline_P8 versus now) for the x and y sweeps (mean and worst cell accuracy, row F1, parent accuracy, accounting pass rate, evaluable_fraction), the ablations and the fault injection.
10. Unchanged on page 4: GT metrics all 1.0, accounting 20/20, examples byte-identical, protected files unchanged (show the git diff --stat against commit 1b6d244 for data/ and examples/).

## B. Close gaps
For every PARTIAL or MISSING item that is small, close it: add the missing tests, add the missing report fields, fix the docs. If a requirement was met in a different but acceptable way, say so and do not rewrite it.

## C. Diagnose the remaining degradation (diagnosis first, change only if principled)
1. At y-jitter 0.2 H and 0.3 H: explain exactly which rows split or merge and why (consecutive-gap threshold versus the within-row spread of two independently jittered words).
2. At x-jitter 0.3 H: attribute the remaining errors to value-column detection versus indent-step clustering versus label token merging (count rows affected per cause over the 20 seeds).
3. If the diagnosis points to thresholds measured in word heights where the relevant separation is a pitch (row pitch for rows, indent pitch for indent steps, column separation for columns), you MAY implement a data-derived threshold (a fraction of the median pitch measured on the page, with a documented minimum and maximum). Keep the change ONLY if: all existing tests pass; page-4 outputs stay byte-identical; the sweeps improve and nothing regresses; and the principle is documented. Otherwise revert it and document the finding as a known limitation. Stop at the first problem. Re-run eval/run_robustness.py and update the before/after table.

## D. Records and finish
- In workstamp.md record that the P10 fixes were applied in a different session and tool, and add P10b to the Prompt history.
- Final commit "P10b: audit of P10 fixes and gap closing"; workstamp.md DONE with "Next action: write-up (P11) and final checks (P13)"; push is NOT required.

## Final message must show
Orientation; the audit table (status per requirement); the gaps closed (with commits); the diagnosis for the y and x degradation; whether a pitch-based threshold was implemented and the before/after sweep numbers (or why not); confirmation of page-4 results and byte-identical examples; test and ruff output; known limitations; open questions.

## Additional notes (these override the sections above where they conflict)
- Since the audit table was drafted, commit 7f5afbd added a seed=11 jitter regression test and the suite has 283 tests. Use the real state.
- In audit item 4, check the robustness markdown and JSON tables specifically: a grep of eval/results/*.md finds evaluable_fraction only in page4_report.md. The tables in robustness_report.md (and its JSON) must show evaluable_fraction (mean and minimum over seeds) next to the accounting pass rate.
- In audit item 5, also confirm there is a regression test for x-jitter 0.3 H seed 1 (two columns, correct roles), not only seed 11 for y.
- Time-box Section C (the pitch-based threshold): if it is not clearly working after about 20 minutes of effort, revert it, keep the diagnosis, and document the limitation. Do not leave the repo in a half-changed state.

## Plan for this prompt

1. [x] Audit real P10 history, source, tests, reports and protected bytes before changes; baseline suite and initial audit table.
2. [x] Close report/coverage gaps and add independent accounting, warnings, geometry and fault-oracle tests without weakening existing tests.
3. [x] Diagnose y=0.2/0.3H and x=0.3H over all seeds; time-box any pitch experiment, keep only with all acceptance conditions met.
4. [x] Regenerate parse/evaluation/robustness, document complete P8/P10/current comparisons and update design/README/audit.
5. [x] Full suite, ruff, determinism/protected checks, final commit and DONE handoff.

## Files created or modified

- notes/p10_audit.md — initial/final audit evidence.
- tests/test_p10b.py — 15 independent acceptance tests.
- src/parser/evaluation/{accounting,metrics,report,robustness}.py — coverage counts/aggregation/headlines/sweep fields.
- src/parser/{rows,hierarchy}.py — one-column/no-body/empty-input warnings.
- eval/results/page4_report.{json,md}; robustness_report.{json,md} — regenerated current reports.
- notes/p10_diagnose.py; p10_geometry_diagnosis.json; p10_pitch_trial.json — reproducible diagnosis and rejected in-memory trial.
- notes/p10_compare.py — reproducible P8/P10/current comparisons.
- README.md; notes/{hierarchy_and_export,evaluation_design,failure_analysis}.md — current rules, warnings, limits and full comparison tables.
- workstamp.md — verbatim P10b request, overrides and plan.

## Last action and result

P10b complete. Final commit f535470cbf737c2db70ea81fa13132ea158be44d.
Audit a46ba5c, validated gap fixes/tests1441dcd, complete diagnosis/
comparison documentation4a03795. No existing fix rewritten or test weakened.
Final audit9 PASS; item5 PARTIAL is an explicitly recorded remaining row split.
P11/P13 not started; no push performed.

Final validation: 298 passed in9.38s (baseline283); ruff check src scripts tests
 eval plus both new diagnostic scripts: All checks passed! git diff --check clean.
All13 protected SHA256 hashes match (GT/raw/examples/P8 artifacts/chat logs).
Fresh parse CLI CSV+JSON byte-identical to examples; GT retains UTF-8 BOM.
All GT metrics1.0; accounting checks/residuals identical to P8,20/20 passing.
Regenerated evaluation JSON/Markdown deterministic. AST comparison confirms
_thresholds and _clusters unchanged from audited P10. Existing tests unchanged;
git diff e40462b -- tests lists only the new test_p10b.py. Audit final9 PASS,
item5 PARTIAL because retained failure-recording test still requires44 rows.

Documentation complete: initial/final audit, preserved P8 table plus full P8/P10/
P10b mean/min grids, six ablations and fault-type/position comparisons. P10b
metrics equal P10; historical P10 regressions at high x/y noise are explicitly
reported. All current reports regenerated. Parse CLI reports43 rows/no warnings.

Section C complete. Reproducible diagnostic records six body split events at
y=.2H and112 at .3H, no merged source groups; x=.3 detects2 correct columns in
all20 seeds but90 row-seed cell assignments differ,81 indent indices and2
parents. No pure label-token spacing/order errors. In-memory pitch candidate
restored43 rows but immediately failed existing seed11 test that requires44;
stopped and restored original function, within minutes of the20-minute budget.
No production threshold change; no candidate-wide sweep claim.

Gap closure: 15 additional acceptance tests, full suite 298 passed in 13.80s;
full-tree ruff clean. Geometry JSON/Markdown now show mean/min evaluable_fraction
beside pass rate; ablations include the companion fraction. Single-page headline
shows pass-rate N/A explicitly. Added no-body/one-column/empty-input warnings.
Independent oracle generates faults and computes residuals inside the test.
Existing test assertions unchanged. Section C diagnosis started; all20 x=.3 seeds
have two correct roles, so remaining numeric errors are the cell-assignment gate.

Clean tree at e40462b. Baseline: 283 passed in 13.23s. History proves baseline
86a290f precedes P10 5565491; seed test added in 7f5afbd. Parser example bytes match;
43 rows, 5 label-rule contras, zero warnings, GT all 1.0, accounting 20/20 and
checks/residuals identical to P8. git diff --stat 1b6d244 -- data/ examples/: empty.
13 protected-file hashes captured including GT/raw/examples/P8 reports/chat logs.

## Decisions and assumptions

P10 fixes were applied in a different session and tool (5565491, 7f5afbd), not by
this auditor. This chat continues the original builder's Session 5. Audit actual
code rather than trusting model attribution in the older log. No source redo.
Keep all existing tests, including seed11's assertion documenting the remaining
44-row failure. No threshold tuned to page4. Optional pitch change stops at first
acceptance failure or about 20 minutes. No push or P11/P13 work in this prompt.

## Known issues / open questions

Seed11 existing test records44 rows rather than requiring intact43-row output.
An in-memory pitch candidate that fixed it failed that gate and was rejected
at the first problem, within the20-minute budget; production thresholds unchanged.
Later authorization is needed to replace the failure-recording assertion before
pursuing a row-split correction. x=.3 cell-assignment/indent limits remain; high
noise P10 tradeoffs are explicitly tabulated. Held-out pages, truncation policy,
and signed/zero diagnostic interval limitations remain open.

## Next action

write-up (P11) and final checks (P13)

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
| P9 | Independent review; 2 major + 3 minor + 5 nit findings; all 14 claims verified; 275 tests pass | 1b6d244 |
| P10 | Apply review fixes with user adjustments; gap-based clustering; 283 tests pass | 7f5afbd |

| P10b | Independent audit; coverage/warnings/oracle tests and comparisons; 298 tests pass; nine PASS, geometry item PARTIAL | f535470cbf737c2db70ea81fa13132ea158be44d |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
| 6 | Claude Sonnet 4.6 (Thinking) | 2026-10-23T10:00:00Z | P9 independent review; read-only for src/tests/eval/scripts/data |
| 7 | Gemini 3.8 Flash | 2026-10-23T10:25:00Z | P10 apply review fixes with user adjustments |

