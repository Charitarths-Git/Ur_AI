# Failure analysis — preserved P8 and current P10b evidence

> Historical P8 baseline: the following original experiment table and
> narrative describe P8. P10 changed clustering/classification/accounting;
> current statuses and complete comparisons follow below. Original parser
> immutability statements here apply to P7–P8 only.

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

<!-- BEGIN P10B COMPARISONS -->
## P10b: measured before/after (P8 → P10 = current P10b)

P8 is the preserved baseline_P8 artifact committed in86a290f before code fixes.
P10 is e40462b's report (including source from5565491/7f5afbd). Current is
the regenerated P10b report. Each cell below is **P8 mean/min → P10 mean/min**;
P10b matches P10 on all five listed metrics at every amplitude. Coverage for
P8/P10 is independently reconstructed from each run's saved status counts;
their files are not rewritten. Undefined fractions/rates exclude that seed
and remain N/A if none are defined. Full defined-run counts are in JSON.

H is median word height. No crashes occurred in any of the360 runs in any version.

### y-axis: full grid, twenty seeds each

| Amplitude H | Cell mean/min | Row F1 mean/min | Parent mean/min | Accounting pass mean/min | evaluable_fraction mean/min |
|---:|---|---|---|---|---|
| 0 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.05 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.1 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.2 | 0.9971/0.9767 → 0.9977/0.9767 | 0.9954/0.9773 → 0.9966/0.9773 | 0.9919/0.9302 → 0.9953/0.9302 | 1.0000/1.0000 → 1.0000/1.0000 | 0.9675/0.9000 → 0.9775/0.9000 |
| 0.3 | 0.5994/0.0000 → 0.8890/0.0000 | 0.9048/0.8367 → 0.9382/0.8866 | 0.9233/0.6512 → 0.9674/0.6512 | 0.9647/0.8182 → 0.9917/0.9000 | 0.5822/0.4444 → 0.6883/0.5000 |
| 0.4 | 0.2890/0.0000 → 0.7221/0.0000 | 0.8214/0.7736 → 0.8629/0.8269 | 0.8105/0.6512 → 0.9291/0.6512 | 0.9775/0.7500 → 0.9900/0.8000 | 0.2809/0.1250 → 0.3649/0.1875 |
| 0.5 | 0.1081/0.0000 → 0.3866/0.0000 | 0.7680/0.7130 → 0.7975/0.7387 | 0.8174/0.6047 → 0.8581/0.6512 | 0.9357/0.5000 → 0.9900/0.8000 | 0.1904/0.0625 → 0.2406/0.0625 |
| 0.75 | 0.0302/0.0000 → 0.1105/0.0000 | 0.6632/0.5664 → 0.6803/0.5660 | 0.6407/0.2791 → 0.6395/0.2326 | 0.8750/0.5000 → 0.7262/0.0000 | 0.0807/0.0000 → 0.0739/0.0000 |
| 1 | 0.0000/0.0000 → 0.0000/0.0000 | 0.5861/0.4211 → 0.5819/0.4444 | 0.4802/0.1860 → 0.4547/0.1395 | 0.3333/0.0000 → 0.4231/0.0000 | 0.0793/0.0000 → 0.0717/0.0000 |

### x-axis: full grid, twenty seeds each

| Amplitude H | Cell mean/min | Row F1 mean/min | Parent mean/min | Accounting pass mean/min | evaluable_fraction mean/min |
|---:|---|---|---|---|---|
| 0 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.05 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.1 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.2 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 | 1.0000/1.0000 → 1.0000/1.0000 |
| 0.3 | 0.3331/0.0000 → 0.9360/0.8488 | 0.9721/0.8837 → 0.9744/0.9302 | 0.9523/0.8837 → 0.9640/0.8837 | 0.9117/0.5714 → 1.0000/1.0000 | 0.4339/0.0500 → 0.7650/0.4000 |
| 0.4 | 0.0401/0.0000 → 0.7750/0.6395 | 0.9616/0.8837 → 0.9058/0.8140 | 0.8570/0.6512 → 0.8756/0.7442 | 0.8558/0.5000 → 1.0000/1.0000 | 0.1060/0.0000 → 0.3502/0.0000 |
| 0.5 | 0.0000/0.0000 → 0.6442/0.5116 | 0.9547/0.8605 → 0.8121/0.6977 | 0.7674/0.5349 → 0.7674/0.6279 | 0.5658/0.0000 → 1.0000/1.0000 | 0.0720/0.0000 → 0.1473/0.0000 |
| 0.75 | 0.0000/0.0000 → 0.4797/0.3721 | 0.9500/0.8605 → 0.6503/0.5581 | 0.5698/0.3721 → 0.2977/0.0698 | 0.3235/0.0000 → 1.0000/1.0000 | 0.0247/0.0000 → 0.0333/0.0000 |
| 1 | 0.0000/0.0000 → 0.3378/0.0000 | 0.9360/0.8372 → 0.5238/0.2558 | 0.4884/0.3488 → 0.2500/0.0930 | 0.1923/0.0000 → 0.0000/0.0000 | 0.0128/0.0000 → 0.0256/0.0000 |

### Structural ablations: P8 → P10 → P10b

Values are single deterministic runs, not averages over seeds. Accounting
coverage is evaluable/applicable, computed from status counts when absent.

| Mode | Cell | Row F1 | Parent | Fully correct | Accounting pass | evaluable_fraction |
|---|---|---|---|---|---|---|
| flatten_indentation | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 0.8837 → 0.8837 → 0.8837 | 0.3256 → 0.3256 → 0.3256 | 0.8333 → 0.8889 → 0.8889 | 0.9000 → 0.9000 → 0.9000 |
| drop_rules | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 |
| translate | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 |
| scale_small | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 |
| scale_large | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 |
| shuffle | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 | 1.0000 → 1.0000 → 1.0000 |

### Fault injection: P8 → P10 → P10b

All versions: numeric-cell participation72/72, faults3817. Detection means
a baseline-passing check becomes fail; no GT is used in this decision.

| Type or digit position (units=0) | P8 detected/total | P10 detected/total | P10b detected/total |
|---|---:|---:|---:|
| blank_to_nil | 71/72 | 71/72 | 71/72 |
| digit_substitution | 3256/3673 | 3256/3673 | 3256/3673 |
| sign_flip | 71/72 | 71/72 | 71/72 |
| 0 | 249/648 | 249/648 | 249/648 |
| 1 | 621/639 | 621/639 | 621/639 |
| 2 | 639/639 | 639/639 | 639/639 |
| 3 | 633/633 | 633/633 | 633/633 |
| 4 | 567/567 | 567/567 | 567/567 |
| 5 | 395/395 | 395/395 | 395/395 |
| 6 | 152/152 | 152/152 | 152/152 |

Fault counts and detector rates are unchanged.417 numeric changes hide within
tolerance;2 faults are numeric no-ops. Default tolerance remains max(1,n).
The new oracle separately checks a hand-written four-addend subtotal plus
gross/contra/net, enumerating its own mutations and direct residuals in the test.

<!-- END P10B COMPARISONS -->

## P10b diagnosis and disposition

P10 improved cell accuracy but did **not** improve every metric. At x=.4/.5/.75/1H,
row F1 means fall .9616→.9058, .9547→.8121, .9500→.6503 and .9360→.5238.
At x=.75/1H, parent means fall .5698→.2977 and .4884→.2500. At y=.75H parent
mean/min fall .6407/.2791→.6395/.2326, accounting mean falls .8750→.7262;
at y=1H parent mean/min fall .4802/.1860→.4547/.1395. These are pre-existing
P10 tradeoffs, not P10b changes. A claim that all cliffs or regressions were
eliminated is unsupported. Cell accuracy alone must not hide those regressions.

| Finding | Current disposition | Measured evidence |
|---|---|---|
| F1 unlisted loss becomes contra | Fixed in P10; verified here | 営業損失 stays line_item, possible_contra_or_loss on row/page/JSON; real page still five label-rule contras and no warnings |
| F2 gross plus contra without net | Fixed in P10; coverage gaps closed here | New nil/invalid/nested tests exercise no-net branch and dependencies; existing net-child tests retained; page accounting checks identical to P8 |
| F3 invisible accounting coverage | Closed in P10b | Geometry JSON/Markdown now include mean/min evaluable_fraction beside pass rate; page/report headlines and ablations show both; zero-applicable and zero-evaluable cases distinguished |
| F4 row splitting | Improved by P10, remains at .2H | P10 y=.3 mean cell .8890 versus P8 .5994; seed11 still splits row24; no P10b threshold change |
| F5 column fragmentation | Improved by P10; assignment gate remains | At x=.3 every seed has two columns/correct roles, but90 row-seed cases lose cell assignment; separate regression verifies seed1 |
| Indent gaps | Still limited | At x=.3 two seeds change81 row-seed indent indices; only seed5 changes two parents, rows14/43 |
| F7/F9 degenerate warnings | Closed in P10b | One-column, empty, no-body cases surface specific warnings in page JSON and CLI tests |
| F8 missing schema columns | Already fixed; preserved | read_table returns Table.issues with clear missing-field messages |
| Flat indentation hierarchy | Unchanged | Parent38/43; paths/full rows still harmed; see ablation table |
| Small numeric faults within tolerance | Unchanged, independently tested | Units249/648, higher3007/3025; arithmetic cannot detect signed-zero/nil no-ops |
| Scanned/multi-page/wrapped/other statements | Still untested | No new backend or held-out documents added |

### y-jitter .2 and .3H: splits, not merges

The diagnosis maps perturbed words back to original word identities, then compares
cluster membership; labels/GT never influence parser decisions. Full row IDs,
labels, seeds, destinations and largest within-row gaps are recorded in
[p10_geometry_diagnosis.json](p10_geometry_diagnosis.json), generated by
`python notes/p10_diagnose.py`.

At .2H there are six body-row split events across six seeds: rows11,19,24,36,38,40,
plus one header split. Seed11 splits the lease accumulated-depreciation row24;
its consecutive centre gap is .350053H, just above the .35H threshold. At .3H
there are112 body-row split events across all20 seeds and seven header splits.
Examples in seed11: rows12,16,17,24,33,38. The exact frequencies for every row
are retained in JSON. **Zero merged source-row groups** occur at either amplitude.

For two independently jittered words, relative movement can approach twice the
amplitude (.4H or .6H). Single linkage fixes running-median fragmentation when
intermediate words bridge the spread, but a sparse two-token row has no bridge.
That explains the remaining split even though typical body pitch is1.338690H.
The synthetic1.3H-pitch test confirms no adjacent row identities merge over its
20 seeds; it does not promise correctness at arbitrary pitch/noise.

### x-jitter .3H: causes counted independently over twenty seeds

Counts below are row-seed cases, so the same physical row can be counted in
several seeds and causes overlap. Unique rows and affected-seed counts are shown
to prevent confusing index shifts with actual hierarchy errors.

| Cause | Row-seed cases | Unique body rows | Affected seeds | Interpretation |
|---|---:|---:|---:|---|
| Wrong number of columns or wrong roles | 0 | 0 | 0 | All20 runs find two correct chronological roles |
| Value assignment differs | 90 | 33 | 18 | Right-edge clusters are intact, but _cells rejects edges farther than .30H from the cluster median |
| Indent-step index differs | 81 | 42 | 2 | Mostly index shifts after splitting a sparse indent cluster; not81 wrong parents |
| Parent identity differs | 2 | 2 | 1 | Seed5, fixed-assets header14 and total43 |
| Pure label-token spacing or order differs | 0 | 0 | 0 | Measured after excluding the original numeric tokens |
| Exported label differs | 90 | 33 | 18 | Rejected numeric tokens remain in the label; this is a consequence of failed cell assignment |

At seed5, two of the original indent anchors near75.24pt split around74.1068 and
77.7889pt: their gap3.6821pt exceeds .40H=3.5856pt. Later indent indices shift;
only two parent links change. Cell assignment still uses distance to the median,
so even a token moved by at most .30H can exceed the gate when that median also
moves. Gap-based column discovery alone does not solve this second gate.

### Bounded pitch experiment: rejected, no production change

The candidate estimated median pitch from provisional row groups (discarding
gaps <=.8H as likely within-row fragments), then used
`max(existing .35H, min(.45 * estimated pitch, .65H))`. The principle was a margin
below half-pitch, with an H-based floor/cap for sparse/noisy estimates. It was an
in-memory experiment only; the original function was restored in a finally block.

The candidate gives43 body rows at y=.2 seed11, but the first acceptance test
`test_measured_failure_seed_11_split` explicitly requires44. It failed immediately.
The user's rules require every existing test to pass and stopping at the first
problem; the test was neither weakened nor edited. The experiment was rejected
within minutes, well inside the20-minute limit. No candidate-wide sweep was run
after that rejection, and no robustness improvement is claimed for it.
[p10_pitch_trial.json](p10_pitch_trial.json) records the failed gate. Production
thresholds remain unchanged; P10b sweep numbers therefore equal audited P10.

Open decision: a later task must explicitly replace this failure-recording
assertion with a correctness assertion before pursuing a row-split repair.
Other open questions remain held-out validation, filing truncation policy and
high-noise chaining/assignment behavior. This audit does not start P11 or P13.
