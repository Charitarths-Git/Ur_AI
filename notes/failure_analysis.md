# Failure analysis: measured development-page experiments

Only the supplied printed page 4 was run. The parser was developed after seeing
it; results are development measurements, not generalisation evidence. No parser
fixes were applied here. Raw PDF, GT, parser production modules and examples are
unchanged. Full seed records and every undetected fault are committed in
eval/results/robustness_report.json; its Markdown companion contains all summaries.

## Observed in experiments

| Failure mode | Measured trigger / affected example | Metrics and accounting symptoms | Root cause / next step for review |
|---|---|---|---|
| A row's label separates from its amounts | First degraded tested y amplitude 0.2 H; seed 11 splits the lease accumulated-depreciation row (GT r024), adding an unlabeled value row | Worst cell score 84/86; one expected contra becomes header; 44 output rows. Two accounting checks become not_evaluable, but evaluable-only accounting pass rate stays 1 | rows.py groups centres within 0.35 H of a running median. Independent ±0.2 H word movement can exceed this separation. Review baseline/overlap grouping and represent missing-value uncertainty; do not silently increase a threshold based on one page |
| Right-edge columns fragment, then chronological roles are lost | First degraded tested x amplitude 0.3 H; seed 1 creates three detected columns and ambiguous_column_roles | That seed has 0/86 expected-role cells, row F1 0.953488, parent 0.953488. Accounting has 9 passes, 21 not_evaluable checks and 3 balance N/A; pass rate is still 1 | column_tolerance is 0.30 H and candidates use running-median clusters. A spread of up to 0.6 H can fragment an anchor. Review robust global column fitting and explicit role/coverage validation |
| Severe jitter collapses useful extraction without crashing | y=1 H: cell mean/worst 0; x>=0.5 H: cell mean/worst 0 in this sweep | Some rows still align by labels/nulls, so row F1 stays much higher than cell accuracy. Accounting rates are undefined for runs with no evaluable checks | A no-crash result is not successful extraction. Track role validity, missing cells, check counts and all metrics together. Never report undefined accounting as a pass |
| Flat indentation loses header nesting | Flatten all body label x0 coordinates | Three sub-section headers (rows 15,31,35) attach to root rather than fixed-assets section; row 42 fixed-assets subtotal attaches to latest header; row 12 allowance attaches to preceding ordinary item | Deliberately partial hierarchy fallback: headers attach to root, subtotal to latest header, contra to nearest ordinary line item. Review richer section-closing/context rules independently, retaining warnings |
| Flat hierarchy harms paths more than immediate parents | Same ablation | Parent 38/43, level 15/43, parent_path 14/43, mean ancestor Jaccard 0.771318, fully correct rows 14/43; values/types still perfect. Accounting 15/18 pass, 3 fail, 2 not_evaluable, 2 N/A | A correct immediate parent may itself sit under a wrong ancestor. Inspect full paths and ancestor metrics, not parent labels alone |
| Missing horizontal rules are warnings rather than extraction failures | Remove every rule | All GT scores and accounting stay 1; ten missing_rule_above warnings (four net, five subtotal, one total) | Label rules still classify these rows. Rule evidence is corroboration, not a requirement or a guarantee of correctness |
| Small digit faults hide under rounding tolerance | Exhaustive one-cell substitutions; 417 undetected numeric changes | Units: 249/648 detected; higher digits: 3007/3025. Eighteen tens-digit changes remain hidden. A 10-addend sum can absorb a units error, and even some changes of 10 | Default tolerance n deliberately permits independent rounding/truncation. Review additional independent checks/precision evidence; tightening tolerance to fit this page alone would create a misleading detector claim |
| Numeric-zero changes cannot be detected arithmetically | Sign flip and nil blanking of the printed negative-zero cell | One sign flip and one blank fault leave the effective sum unchanged; both remain in fault denominators and are tagged no_numeric_change | Preserve raw/status comparisons for representation correctness. Arithmetic alone cannot distinguish 0, signed zero and a nil interpreted as zero in sums |

All 360 geometry attempts (two axes × nine amplitudes × twenty seeds) completed
without a parser crash. No seeds were reduced; runtime was well under a couple
of minutes. Translate, both scales (0.45 and 2.75) and shuffled word order retained
all GT scores at 1. These are the tested transformations, not a broader guarantee.

## Threshold interpretation

H=8.963989 pt; row tolerance=0.35 H=3.137396 pt; column tolerance=0.30 H=2.689197 pt;
indent tolerance=0.40 H=3.585596 pt. A jitter amplitude is a bound on each word's
translation independently, so relative separation can be twice the amplitude.
The first degraded *tested* amplitude is not a mathematical failure boundary:
we tested only the requested grid and seeds. y is perfect through 0.1 H; x is
perfect through 0.2 H on this page. At high x jitter the indent clusters can
also drift/merge, adding hierarchy errors after column failures have begun.

## Accounting detector coverage and blind spots

All 72 printed numeric cells participate in at least one baseline-passing check.
The two printed nil cells are excluded from this numeric-fault population, and
headers are excluded. Exhaustive faults: 3673 digit substitutions, 72 sign flips,
72 nil blanks, total 3817. Detection is specifically a baseline-passing check
becoming fail; warnings or not_evaluable alone are not counted as detection.

Detection: digits 3256/3673; sign flips 71/72; nil blanks 71/72. Of 419 undetected
faults, 417 change a number while every affected check remains inside tolerance;
two do not change the effective numeric contribution. Hidden faults involve
checks with n=2,3,5,6,10; the JSON groups every affected n combination.

Concrete example: row 3 previous-year amount 2,002,429 changed to 2,002,439.
Its 10-addend subtotal residual moves from +3 to -7, still inside ±10, so it is
not detected. Changing its units digit from 9 to 2 instead gives residual +10,
exactly on the allowed boundary. This is why a last-digit error in a sum with
many addends can slip under the tolerance even with 100% check participation.

Accounting pass rate uses only evaluable checks. Every sweep summary also stores
defined-run counts and statuses; at y=0.75 H only 14/20 runs have a defined rate,
and at x=1 H only 13/20 do. A high remaining pass rate can coexist with badly
damaged extraction because checks disappeared or became not_evaluable. It is
consistency evidence, not correctness or detector recall on arbitrary errors.

## Expected but not tested

- Scanned pages/OCR noise: no OCR/VLM backend or image degradation experiment.
- Tables spanning pages: no cross-page stitching or multi-page evaluation.
- Wrapped labels and multi-line units/headers: known geometry limitations, not measured here.
- Multiple tables on one page: no segmentation experiment.
- Other Japanese statements, liability/equity sections, other units and languages:
  unvalidated RuleSet heuristics, not a measured generalisation set.
- Multiple simultaneous faults, correlated errors, changes to row IDs/types or
  parent links as fault injection: not part of the exhaustive one-numeric-cell design.
- The requested truncation interval is a hypothesis diagnostic on this page,
  not proof of the filing's rounding policy. Signed/zero edge cases need care.

## Recommended independent review

Review file-reader/schema failure behavior, alignment ambiguity and denominators,
identity-aware parent scoring, missing/invalid accounting inputs and tolerance
tradeoffs before changing parser rules. Preserve this measured baseline; apply
any parser fixes only after the independent review phase.
