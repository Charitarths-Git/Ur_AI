# Robustness experiments — one development page

Seeds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]. Jitter units: median word height.

## Geometry sweep

Each entry is mean / worst. See JSON for all seed records and defined-run counts.

| Axis | H amplitude | Cell accuracy | Row F1 | Parent accuracy | Accounting pass rate | Crashes |
|---|---:|---:|---:|---:|---:|---:|
| y | 0 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.05 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.1 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| y | 0.2 | 0.9971 / 0.9767 | 0.9954 / 0.9773 | 0.9919 / 0.9302 | 1.0000 / 1.0000 | 0 |
| y | 0.3 | 0.5994 / 0.0000 | 0.9048 / 0.8367 | 0.9233 / 0.6512 | 0.9647 / 0.8182 | 0 |
| y | 0.4 | 0.2890 / 0.0000 | 0.8214 / 0.7736 | 0.8105 / 0.6512 | 0.9775 / 0.7500 | 0 |
| y | 0.5 | 0.1081 / 0.0000 | 0.7680 / 0.7130 | 0.8174 / 0.6047 | 0.9357 / 0.5000 | 0 |
| y | 0.75 | 0.0302 / 0.0000 | 0.6632 / 0.5664 | 0.6407 / 0.2791 | 0.8750 / 0.5000 | 0 |
| y | 1.0 | 0.0000 / 0.0000 | 0.5861 / 0.4211 | 0.4802 / 0.1860 | 0.3333 / 0.0000 | 0 |
| x | 0 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.05 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.1 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.2 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 1.0000 / 1.0000 | 0 |
| x | 0.3 | 0.3331 / 0.0000 | 0.9721 / 0.8837 | 0.9523 / 0.8837 | 0.9117 / 0.5714 | 0 |
| x | 0.4 | 0.0401 / 0.0000 | 0.9616 / 0.8837 | 0.8570 / 0.6512 | 0.8558 / 0.5000 | 0 |
| x | 0.5 | 0.0000 / 0.0000 | 0.9547 / 0.8605 | 0.7674 / 0.5349 | 0.5658 / 0.0000 | 0 |
| x | 0.75 | 0.0000 / 0.0000 | 0.9500 / 0.8605 | 0.5698 / 0.3721 | 0.3235 / 0.0000 | 0 |
| x | 1.0 | 0.0000 / 0.0000 | 0.9360 / 0.8372 | 0.4884 / 0.3488 | 0.1923 / 0.0000 | 0 |

First degraded tested amplitude: {'y': 0.2, 'x': 0.3}.

## Structural ablations

The JSON includes the full metric set and accounting checks for each.

| Mode | Cell accuracy | Row F1 | Parent | Full rows | Accounting | Parser warnings |
|---|---:|---:|---:|---:|---:|---:|
| flatten_indentation | 1.0000 | 1.0000 | 0.8837 | 0.3256 | 0.8333 | 1 |
| drop_rules | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 10 |
| translate | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| scale_small | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| scale_large | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| shuffle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |

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
