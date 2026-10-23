# Robustness experiments — one development page

Seeds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]. Jitter units: median word height.

Baseline accounting pass rate=1.0000; evaluable_fraction=1.0000.

## Geometry sweep

Each entry is mean / minimum over defined seeds. See JSON for all seed records and defined-run counts.

| Axis | H amplitude | Cell accuracy | Row F1 | Parent accuracy | Accounting pass rate | evaluable_fraction | Crashes |
|---|---:|---:|---:|---:|---:|---:|---:|
| y | 0 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.05 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.1 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.2 | 0.9977 / 0.9767 | 0.9966 / 0.9773 | 0.9953 / 0.9302 | 1.0000 / 1.0000 | 0.9775 / 0.9000 | 0 |
| y | 0.3 | 0.8890 / 0.0000 | 0.9382 / 0.8866 | 0.9674 / 0.6512 | 0.9917 / 0.9000 | 0.6883 / 0.5000 | 0 |
| y | 0.4 | 0.7186 / 0.0000 | 0.8592 / 0.8081 | 0.8767 / 0.5814 | 0.9900 / 0.8000 | 0.3572 / 0.1875 | 0 |
| y | 0.5 | 0.3843 / 0.0000 | 0.7906 / 0.7387 | 0.7535 / 0.5814 | 0.9900 / 0.8000 | 0.2351 / 0.0625 | 0 |
| y | 0.75 | 0.1093 / 0.0000 | 0.6757 / 0.5660 | 0.5767 / 0.2326 | 0.7262 / 0.0000 | 0.0697 / 0.0000 | 0 |
| y | 1.0 | 0.0000 / 0.0000 | 0.5783 / 0.4444 | 0.4337 / 0.1395 | 0.4231 / 0.0000 | 0.0717 / 0.0000 | 0 |
| x | 0 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.05 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.1 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.2 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.3 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0.9977 / 0.9535 | 0.9950 / 0.9000 | 1.0000 / 1.0000 | 0 |
| x | 0.4 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0.9953 / 0.9535 | 0.9950 / 0.9000 | 0.9900 / 0.8000 | 0 |
| x | 0.5 | 0.9884 / 0.9070 | 0.9953 / 0.9535 | 0.9826 / 0.9302 | 0.9744 / 0.8889 | 0.9297 / 0.6875 | 0 |
| x | 0.75 | 0.8256 / 0.7674 | 0.9349 / 0.8837 | 0.4233 / 0.0930 | 0.9481 / 0.4286 | 0.1185 / 0.0000 | 0 |
| x | 1.0 | 0.5535 / 0.0000 | 0.7899 / 0.5476 | 0.3081 / 0.1395 | 0.7083 / 0.0000 | 0.0661 / 0.0000 | 0 |

First degraded tested amplitude: {'y': 0.2, 'x': 0.3}.

## Structural ablations

The JSON includes the full metric set and accounting checks for each.

| Mode | Cell accuracy | Row F1 | Parent | Full rows | Accounting pass rate | evaluable_fraction | Parser warnings |
|---|---:|---:|---:|---:|---:|---:|---:|
| flatten_indentation | 1.0000 | 1.0000 | 0.8837 | 0.3256 | 0.8889 | 0.9000 | 1 |
| drop_rules | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 10 |
| translate | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| scale_small | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| scale_large | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| shuffle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |

## Exhaustive parsed-value fault injection

Coverage: 72/72; generated faults: 3817.

| Fault | Detected | Total | Rate |
|---|---:|---:|---:|
| blank_to_nil | 71 | 72 | 0.9861 |
| digit_substitution | 3256 | 3673 | 0.8865 |
| sign_flip | 71 | 72 | 0.9861 |

| Digit position from units | Detected | Total | Rate |
|---|---:|---:|---:|
| 0 | 249 | 648 | 0.3843 |
| 1 | 621 | 639 | 0.9718 |
| 2 | 639 | 639 | 1.0000 |
| 3 | 633 | 633 | 1.0000 |
| 4 | 567 | 567 | 1.0000 |
| 5 | 395 | 395 | 1.0000 |
| 6 | 152 | 152 | 1.0000 |

Units vs higher digits: {'units': {'detected': 249, 'total': 648, 'rate': 0.38425925925925924}, 'higher': {'detected': 3007, 'total': 3025, 'rate': 0.9940495867768595}}.
Undetected reasons: {'no_numeric_change': 2, 'within_tolerance': 417}.
Within-tolerance faults grouped by impacted addend counts: {'10': 190, '2': 73, '2,10': 7, '2,3': 12, '2,6': 27, '3,5': 6, '3,6': 9, '5': 67, '6': 26}.

Every undetected fault and its impacted n/residual/tolerance are listed in JSON.
A last-digit error can hide inside a many-addend sum's tolerance. Printed-zero sign flips and blanking zero do not change arithmetic.

## Limitations

- Single development page, not a generalisation claim.
- Uniform per-word translation jitter, not OCR image noise; rules remain unjittered.
- Crash runs count as zero for GT sweep scores; undefined accounting rates are excluded with defined_runs reported.
- First degraded tested amplitude is not a universal geometric bound.
- Existing parser bugs are documented, not fixed here.
