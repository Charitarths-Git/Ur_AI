# P10b independent audit

## Before-change evidence (e40462b)

283 tests passed in 13.23s. P10 was applied in a different session/tool, in
5565491; 7f5afbd adds the seed11 test. This audit does not redo those fixes.

| # | Initial status | Evidence before changes | Gap to close |
|---|---|---|---|
| 1 | PASS | git log: 86a290f preserves baseline_P8 before 5565491; four files match P8 reports | None |
| 2 | PARTIAL | accounting.py:72-95 implements net/own+contras/header; test_gross_with_contra_child_and_no_net_row_contributes_gross_plus_contra and existing nested net test pass; page checks identical to P8 | Missing nil/invalid/nested tests for the NEW no-net branch |
| 3 | PARTIAL | classify.py:53-75 and test_loss_row_warns_possible_contra_or_loss; real page 5 label-rule contras, zero warnings | Page propagation test missing; hierarchy_and_export.md still says structural negatives become contra |
| 4 | PARTIAL | accounting.py:173-197 has fraction, empty/mixed tests; page4_report.md:75 shows fraction; robustness.py PRIMARY excludes it | Missing geometry JSON/Markdown mean/min fraction, ablation companion, explicit headline N/A and zero-evaluable-applicable case |
| 5 | PARTIAL | rows.py:46 shared gap helper called at190/103/244; invariance suite passes; test_measured_failure_seed_11_split asserts44 rows | No x=.3 seed1 regression, no 1.3H-pitch jitter test; y test records failure rather than fixes it |
| 6 | PARTIAL | rows.py:248 no_columns_detected; test_reconstruct_page_no_columns_warning | No explicit one-column warning; empty hierarchy still insufficient_indentation; integration tests missing |
| 7 | PARTIAL | test_exhaustive_fault_population_and_detector_are_deterministic derives real digit counts; toy test calls iter_faults/apply_fault/accounting_checks | Toy is not an independent oracle and has no net row; add independent generator + arithmetic |
| 8 | PASS | data.py:43-60 returns Table issues for missing schema/raw fields; test_evaluation.py missing-schema test | Existing malformed row identities still raise, outside this schema-only requirement |
| 9 | MISSING | git show --stat5565491 has no README/evaluation_design/failure_analysis; these still describe P8 | Add full P8/P10/current sweep, ablation, fault comparisons and current rules |
| 10 | PASS | git diff --stat1b6d244 -- data/ examples/ empty; fresh parse bytes identical; evaluate_files gives all1.0; full accounting_checks equal baseline_P8 | Preserve and recheck |

P8 preservation content and source-history ordering are acceptable. Do not
rewrite successful P10 fixes. Original tests remain intact, including the
seed11 failure-recording regression. Initial statuses above remain historical;
final acceptance and remaining limitations are recorded below after validation.
