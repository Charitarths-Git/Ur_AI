# Development evaluation: supplied page 4

## Metrics and denominators

| Metric | Correct / denominator | Score | Meaning |
|---|---:|---:|---|
| label_exact | 43 / 43 | 1.000000 | exact printed labels / all GT rows (missing rows wrong) |
| label_key | 43 / 43 | 1.000000 | matching label_key / all GT rows |
| row_type | 43 / 43 | 1.000000 | correct row types / all GT rows |
| level | 43 / 43 | 1.000000 | correct ancestor-count levels / all GT rows |
| parent | 43 / 43 | 1.000000 | parents mapped by row alignment (both roots correct) / all GT rows |
| parent_path | 43 / 43 | 1.000000 | exact printed ancestor paths / all GT rows |
| ancestor_jaccard | 43.0 / 43 | 1.000000 | sum of alignment-mapped ancestor-set Jaccards / all GT rows |
| fully_correct_rows | 43 / 43 | 1.000000 | exact label, both/all values, type, mapped parent and level / all GT rows |
| cell_accuracy_all | 86 / 86 | 1.000000 | correct integer/null cells / all GT row-column cells |
| cell_accuracy_printed | 74 / 74 | 1.000000 | correct integer/null cells / GT cells with nonempty raw |
| raw_accuracy | 86 / 86 | 1.000000 | identical raw strings / all GT row-column cells |
| row_precision | 43 / 43 | 1.000000 | aligned rows / predicted rows |
| row_recall | 43 / 43 | 1.000000 | aligned rows / GT rows |
| row_f1 | 86 / 86 | 1.000000 | 2 * aligned rows / (prediction rows + GT rows) |
| column_roles | 2 / 2 | 1.000000 | correct role at each unique expected column index / max(expected,predicted columns); optional JSON/meta |
| column_periods | 2 / 2 | 1.000000 | correct date at each unique expected column index / max(expected,predicted columns); optional JSON/meta |

Undefined denominators are N/A, not perfect scores. Missing GT rows count as wrong.

## Alignment

Matched 43 rows; prediction=43, GT=43. Threshold=0.5.

## Type confusion matrix

| GT \ predicted | contra | header | line_item | net | subtotal | total |
|---|---:|---:|---:|---:|---:|---:|
| contra | 5 | 0 | 0 | 0 | 0 | 0 |
| header | 0 | 6 | 0 | 0 | 0 | 0 |
| line_item | 0 | 0 | 22 | 0 | 0 | 0 |
| net | 0 | 0 | 0 | 4 | 0 | 0 |
| subtotal | 0 | 0 | 0 | 0 | 5 | 0 |
| total | 0 | 0 | 0 | 0 | 0 | 1 |

## Every mismatch

None.

## Label-free accounting

Residual = printed minus expected; tolerance = max(1, number of addends).
Nil raw marks alone allow a null to contribute zero; invalid/empty amounts are not evaluable.

| Kind | Row | Column | n | Expected | Printed | Residual | Tolerance | Status | Truncation interval | Inside |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| subtotal | 13 | previous_year | 10 | 5863681 | 5863684 | 3 | 10 | within_tolerance | [-1,8] | True |
| subtotal | 13 | current_year | 10 | 3377405 | 3377407 | 2 | 10 | within_tolerance | [0,8] | True |
| net | 18 | previous_year | 2 | 197775 | 197775 | 0 | 2 | exact | [-1,0] | True |
| net | 18 | current_year | 2 | 239829 | 239828 | -1 | 2 | within_tolerance | [-1,0] | True |
| net | 21 | previous_year | 2 | 390757 | 390757 | 0 | 2 | exact | [-1,0] | True |
| net | 21 | current_year | 2 | 336708 | 336708 | 0 | 2 | exact | [-1,0] | True |
| net | 25 | previous_year | 2 | 63147 | 63146 | -1 | 2 | within_tolerance | [-1,0] | True |
| net | 25 | current_year | 2 | 41873 | 41872 | -1 | 2 | within_tolerance | [-1,0] | True |
| net | 29 | previous_year | 2 | 8439 | 8439 | 0 | 2 | exact | [-1,0] | True |
| net | 29 | current_year | 2 | 24243 | 24243 | 0 | 2 | exact | [-1,0] | True |
| subtotal | 30 | previous_year | 6 | 1429093 | 1429094 | 1 | 6 | within_tolerance | [0,4] | True |
| subtotal | 30 | current_year | 6 | 1352607 | 1352610 | 3 | 6 | within_tolerance | [0,5] | True |
| subtotal | 34 | previous_year | 2 | 44260 | 44261 | 1 | 2 | within_tolerance | [0,1] | True |
| subtotal | 34 | current_year | 2 | 35868 | 35869 | 1 | 2 | within_tolerance | [0,1] | True |
| subtotal | 41 | previous_year | 5 | 197068 | 197069 | 1 | 5 | within_tolerance | [0,3] | True |
| subtotal | 41 | current_year | 5 | 369361 | 369362 | 1 | 5 | within_tolerance | [0,4] | True |
| subtotal | 42 | previous_year | 3 | 1670424 | 1670426 | 2 | 3 | within_tolerance | [0,2] | True |
| subtotal | 42 | current_year | 3 | 1757841 | 1757841 | 0 | 3 | exact | [0,2] | True |
| total | 43 | previous_year | 2 | 7534110 | 7534110 | 0 | 2 | exact | [0,1] | True |
| total | 43 | current_year | 2 | 5135248 | 5135249 | 1 | 2 | within_tolerance | [0,1] | True |
| balance | — | previous_year | 0 | — | — | — | — | not_applicable | N/A | — |
| balance | — | current_year | 0 | — | — | — | — | not_applicable | N/A | — |

Accounting passes: 20/20; statuses={'exact': 7, 'within_tolerance': 13, 'fail': 0, 'not_evaluable': 0, 'not_applicable': 2}.
Truncation interval consistency: 20/20. This is a hypothesis diagnostic, never a pass/fail criterion.

## Limitations of this evaluation

- Single page only; micro and macro averages coincide for this one page.
- Parser rules were designed after seeing this page: development results, NOT a generalisation claim.
- GT was drafted by an AI agent and verified by one human; the user also reported an independent second review.
- The truncation hypothesis rests on one page and must be verified by the human; it does not set pass/fail.
- Alignment can be ambiguous for identical repeated labels/values; earliest-pair ties do not prove identity.
- Accounting tests consistency of predicted structure, not truth; absent or wrong checks can escape detection.
