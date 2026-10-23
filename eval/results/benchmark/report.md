# Provisional additional-page benchmark

AI-drafted image annotations; NOT independently checked or human verified. Five issuers in one industry; four similarly styled templates. No broad generalisation claim.

| Page | Split | Engine | Cells | Labels (normalized) | Parents | Full rows | Missing/extra | Median / IQR ms |
|---|---|---|---|---|---|---|---|---|
| supplied | supplied_development | original | 86/86 | 43/43 | 43/43 | 43/43 | 0/0 | 17.11 / 2.39 |
| supplied | supplied_development | candidate | 86/86 | 43/43 | 43/43 | 43/43 | 0/0 | 16.97 / 4.27 |
| supplied | supplied_development | pdfplumber | 82/86 | 39/43 | N/A | N/A | 2/0 | 102.49 / 2.76 |
| nintendo | development | original | 58/58 | 29/29 | 29/29 | 26/29 | 0/0 | 44.71 / 5.25 |
| nintendo | development | candidate | 58/58 | 29/29 | 29/29 | 26/29 | 0/0 | 44.45 / 0.74 |
| nintendo | development | pdfplumber | 54/58 | 27/29 | N/A | N/A | 2/0 | 121.02 / 5.64 |
| capcom | development | original | 60/60 | 30/30 | 30/30 | 24/30 | 0/0 | 20.19 / 3.35 |
| capcom | development | candidate | 60/60 | 30/30 | 30/30 | 24/30 | 0/0 | 18.88 / 3.04 |
| capcom | development | pdfplumber | 56/60 | 26/30 | N/A | N/A | 2/0 | 122.06 / 1.93 |
| sega | held_out | original | 90/90 | 45/45 | 45/45 | 45/45 | 0/0 | 24.91 / 1.59 |
| sega | held_out | candidate | 90/90 | 45/45 | 45/45 | 45/45 | 0/0 | 24.55 / 3.01 |
| sega | held_out | pdfplumber | 86/90 | 27/45 | N/A | N/A | 2/0 | 180.96 / 19.66 |
| square | held_out | original | 80/80 | 40/40 | 40/40 | 40/40 | 0/0 | 11.77 / 1.53 |
| square | held_out | candidate | 80/80 | 40/40 | 40/40 | 40/40 | 0/0 | 13.70 / 1.02 |
| square | held_out | pdfplumber | 76/80 | 24/40 | N/A | N/A | 2/0 | 424.13 / 10.69 |
| konami | held_out | original | 92/92 | 46/46 | 46/46 | 44/46 | 0/0 | 40.67 / 0.68 |
| konami | held_out | candidate | 92/92 | 46/46 | 46/46 | 44/46 | 0/0 | 41.78 / 0.28 |
| konami | held_out | pdfplumber | 88/92 | 38/46 | N/A | N/A | 2/0 | 101.46 / 4.17 |

## Pooled counts and per-page means

| Split | Engine | Pooled cells | Mean page cell score | Pooled parents | Mean page parent score |
|---|---|---|---|---|---|
| supplied_development | original | 86/86 | 1.0 | 43/43 | 1.0 |
| supplied_development | candidate | 86/86 | 1.0 | 43/43 | 1.0 |
| supplied_development | pdfplumber | 82/86 | 0.9534883720930233 | N/A | None |
| development | original | 118/118 | 1.0 | 59/59 | 1.0 |
| development | candidate | 118/118 | 1.0 | 59/59 | 1.0 |
| development | pdfplumber | 110/118 | 0.9321839080459771 | N/A | None |
| held_out | original | 262/262 | 1.0 | 131/131 | 1.0 |
| held_out | candidate | 262/262 | 1.0 | 131/131 | 1.0 |
| held_out | pdfplumber | 250/262 | 0.9540257648953301 | N/A | None |

## Failures and warnings (all selected pages retained)

- supplied / original: usable; warnings=[]; mismatches=0.
- supplied / candidate: usable; warnings=[]; mismatches=0.
- supplied / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=229.
- nintendo / original: usable; warnings=[]; mismatches=3.
- nintendo / candidate: usable; warnings=[]; mismatches=3.
- nintendo / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=157.
- capcom / original: usable; warnings=[]; mismatches=6.
- capcom / candidate: usable; warnings=[]; mismatches=6.
- capcom / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=164.
- sega / original: usable; warnings=[]; mismatches=0.
- sega / candidate: usable; warnings=[]; mismatches=0.
- sega / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=253.
- square / original: usable; warnings=[]; mismatches=0.
- square / candidate: usable; warnings=[]; mismatches=0.
- square / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=226.
- konami / original: usable; warnings=[]; mismatches=2.
- konami / candidate: usable; warnings=[]; mismatches=2.
- konami / pdfplumber: usable_with_warnings; warnings=['hierarchy_and_row_types_unsupported', 'chronology_assumed_left_to_right']; mismatches=245.

Full per-page counts, raw/printed-cell metrics, every mismatch, pooled and per-page-average denominators, package/hardware details and individual timings are in report.json. Baseline structural metrics are N/A, not correct. New issuers use million-yen units; supplied page uses thousand-yen units. An asset-only page is not a complete statement.

Reproduce: python scripts/run_benchmark.py --download --render
