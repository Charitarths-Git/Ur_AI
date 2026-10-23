# P10b audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit

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


## Final acceptance

| # | Final status | Evidence / disposition |
|---|---|---|
| 1 | PASS | 86a290f precedes5565491; preserved P8 artifacts retained byte-for-byte |
| 2 | PASS | Existing net-priority test retained; test_no_net_contra_nil_invalid_and_nested_header (four cases) plus invalid-gross test; identical20 page checks |
| 3 | PASS | test_loss_warning_propagates_from_row_to_page_json; page still five label-rule contras/zero warnings; hierarchy_and_export RuleSet/evidence section corrected |
| 4 | PASS | robustness.py PRIMARY now includes coverage; every geometry summary stores mean/worst(min), every seed stores fraction; committed Markdown and JSON validated by test_committed_robustness_coverage_mean_min_and_markdown; ablation companion and both headlines present; N/A and mixed/zero cases tested |
| 5 | PARTIAL | Shared gap helper/invariance verified; x .3 seed1 regression and1.3H pitch test added. Existing seed11 test preserved: it records44-row failure, not intact row. Optional pitch trial rejected at its first acceptance failure, so known y split remains |
| 6 | PASS | one_column_detected/no_body_rows/empty_input added; tests cover one-column/empty/no-body JSON and CLI warning output; no misleading insufficient_indentation for empty input |
| 7 | PASS | test_independent_fault_oracle_four_addends_and_net enumerates mutations and computes residuals inside test without library generation/check calls; existing real-page digit-derived population assertion retained |
| 8 | PASS | Existing missing-schema Table.issues implementation/test retained; no rewrite of accepted fix |
| 9 | PASS | README/design/rule notes updated; failure_analysis preserves P8 and adds complete18-row-grid mean/min tables for every requested score, all six ablations, fault types/positions; high-noise regressions explicitly called out |
| 10 | PASS | Fresh parse bytes and GT metrics/accounting rechecked; git diff --stat1b6d244 -- data/ examples/ remains empty; protected SHA256 comparison recorded in workstamp |

Gap commit1441dcd adds15 tests and coverage/warning fixes. No pre-existing test
was edited, weakened or deleted. Initial independent oracle audit found the old
toy test reused library logic; it is kept and supplemented, not relabeled as
independent. No second truncation model was added: it was optional P10 scope and
is unnecessary for this audit.

Section C stopped on the first problem, well within20 minutes: the pitch candidate
would return43 rows, while existing test_measured_failure_seed_11_split requires44.
The candidate was an in-memory override restored in finally; production thresholds
are unchanged. This is not evidence of general pitch-model robustness, and no
candidate-wide sweep is claimed. A later task must explicitly authorize replacing
the failure-recording test before implementing a row-split correction.


Final verification: **298 passed in9.38s**, baseline283. Full-tree ruff and both
new diagnostic scripts: **All checks passed!** git diff --check clean. All13
protected SHA256 hashes match (GT/raw/examples/P8 artifacts/chat logs); GT keeps
UTF-8 BOM. Fresh CLI exports are byte-identical; every GT metric1.0 and all20
accounting checks/residuals match P8. Evaluation JSON/Markdown regeneration is
identical. AST of _thresholds/_clusters matches audited P10 exactly. git diff
--stat1b6d244 -- data/ examples/ is empty. The only P10b tests diff is new
`tests/test_p10b.py`; every old assertion remains intact.
