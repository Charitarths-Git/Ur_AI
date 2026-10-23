# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P10 |
| State | DONE |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T10:45:00Z |

## Current prompt (verbatim)

The P9 review is good and nobody needs to redo it. On a read-through the summary is credible: it verified 14 builder claims by running things (clean-clone install, determinism, protected files, GT-leak, test-weakening) and found two real major defects. I also checked the two worked examples in failure_analysis.md by hand (changing 2,002,429 to 2,002,439 moves the 10-addend residual from +3 to −7, and the units-digit case lands exactly on the ±10 boundary) and both hold.

The review’s fix list needs three adjustments before it goes to Codex.

F2 (gross item with a contra child but no net row). The list says “document + add test”. That leaves a known false-failure bug in place. It’s a small fix: the contribution should be gross plus its contra children when there’s no net row. P10 below implements it.
F10 (chat_logs/). Don’t add it to .gitignore. Your chat logs are a required deliverable, and ignoring the folder wouldn’t remove the 430 KB transcript from git history anyway. P10 skips this fix, and you handle it manually (steps below).
F4 and F5 are the same weakness, and F5 (columns) isn’t in the fix list as its own item. The cliff at x-jitter 0.3 H comes from the same running-median clustering as the y-jitter cliff. P10 replaces it with gap-based clustering for rows and columns together, then re-measures both sweeps. If the numbers don’t improve, the report has to say so.

I also added a small independent test: a brute-force check of the fault-injection detection logic on a toy tree. The review didn’t read faults.py, perturb.py or robustness.py, and those produce your headline detection numbers.

The review also found two things to keep for your write-up: the loss-row misclassification (営業損失 becomes contra) and the missing coverage metric.

do the above work quickly and give a respinse

## Plan for this prompt (P10)

1. [x] F1: Fix structural contra fallback in classify.py (classify as line_item with possible_contra_or_loss warning when not matching contra_labels). Add tests.
2. [x] F2: Fix accounting contribution in accounting.py when gross item has contra children but no net child. Add tests.
3. [x] F3: Add evaluable_fraction to accounting_summary() and update markdown_report(). Add tests.
4. [x] F4 + F5: Replace running-median clustering in rows.py with gap-based clustering for both rows and columns. Verify existing tests pass.
5. [x] F8: Structured schema error handling in read_table() in data.py instead of raising ValueError. Add tests.
6. [x] F9: Emit no_columns_detected warning when centres is empty in reconstruct_page(). Add tests.
7. [x] Brute-force fault injection test on a toy tree (in test_perturbation.py and review_probes.py).
8. [x] Re-run eval and robustness sweep, update eval/results/ and record impact.
9. [x] Run full test suite and ruff checks (282 passed, ruff clean).
10. [x] Final commit "P10: apply review fixes", update workstamp.md to DONE, push.

## Files created or modified

- src/parser/classify.py — F1: all-negative fallback classifies as line_item with possible_contra_or_loss ParseWarning.
- src/parser/evaluation/accounting.py — F2: gross with contra children and no net child contributes gross + contras; F3: evaluable_fraction in accounting_summary.
- src/parser/evaluation/data.py — F8: read_table returns Table with issues on missing CSV fields instead of raising ValueError.
- src/parser/evaluation/report.py — F3: display evaluable_fraction in markdown_report.
- src/parser/export.py — forward layout.warnings into ParsedPage.warnings.
- src/parser/layout_types.py — define ParseWarning and add warnings field to PageLayout.
- src/parser/rows.py — F4/F5: gap-based clustering in _clusters(); F9: emit no_columns_detected warning when centres is empty.
- eval/results/page4_report.json, eval/results/page4_report.md — regenerated with evaluable_fraction.
- eval/results/robustness_report.json, eval/results/robustness_report.md — regenerated with gap-based clustering sweeps.
- tests/test_accounting.py — tests for F2 contribution and F3 evaluable_fraction.
- tests/test_evaluation.py — test for F8 read_table structured schema errors.
- tests/test_hierarchy.py — tests for F1 loss-row classification and warning.
- tests/test_perturbation.py — brute-force fault injection check on a toy tree.
- tests/test_rows.py — test for F9 no_columns_detected warning.
- notes/review_probes.py — added PROBE 9 (brute force toy tree fault injection).
- workstamp.md — updated to DONE with P10 history.

## Last action and result

P10 complete. All review fixes and user adjustments implemented and verified:
1. F1: classify.py correctly classifies rows with all-negative cells and no contra label prefix as line_item with possible_contra_or_loss warning. Probe 1 confirmed 営業損失 -> line_item.
2. F2: accounting.py calculates gross + contra children when no net child exists; subtotal receives expected net-of-contra sum; passes exact.
3. F3: accounting_summary() returns evaluable_fraction and reports it in Markdown and JSON.
4. F4 + F5: rows.py _clusters replaced running-median with gap-based clustering. Robustness sweep re-run:
   - x-jitter cell accuracy at 0.3H improved from 0.3331 (worst 0.0000) to 0.9360 (worst 0.8488)!
   - x-jitter cell accuracy at 0.4H improved from 0.0401 to 0.7750!
   - y-jitter cell accuracy at 0.3H improved from 0.5994 to 0.8890!
   - y-jitter cell accuracy at 0.4H improved from 0.2890 to 0.7221!
   - Catastrophic cliffs eliminated; first tested degraded amplitude remains {'y': 0.2, 'x': 0.3}.
5. F8: data.py read_table returns structured issues for missing columns.
6. F9: rows.py reconstruct_page emits no_columns_detected warning on empty column detection.
7. Brute-force fault injection test on a toy tree added to test_perturbation.py and notes/review_probes.py: confirms 78/84 faults detected, 100% of hundreds digit faults detected, units digit faults slip under tolerance as expected.
8. Test suite: 282 passed (baseline 275 + 7 new tests). Full ruff check clean.
9. Protected files (data/, data/raw/, data/gt/) unchanged. F10 (chat_logs) untouched per instruction.

## Decisions and assumptions

- F10: chat_logs/ not ignored; preserved as required deliverable.
- Gap-based clustering used for both rows and columns in _clusters.
- Loss-row misclassification and coverage metric documented for P11 write-up.

## Known issues / open questions

- Document loss-row misclassification and coverage metric in P11 write-up.

## Next action

P11 write-up

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

