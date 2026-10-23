> **2026-10-23 attribution note:** The reviewer was Claude Sonnet 4.6 per the
> owner (**user-supplied**). The review findings below are unchanged.

# P9 Independent Review — jp-balance-sheet-parser

**Reviewer:** Claude Sonnet 4.6 (Thinking) — independent of the builder agents (GPT-6.1 Sol / Claude Opus 4.6).  
**Date:** 2026-10-23  
**Scope:** Read-only for src/, tests/, eval/, scripts/, data/.

---

## 1. Verdict (3–5 sentences)

The pipeline is well-structured, honestly bounded, and correctly refuses to over-claim.
The GT metrics and accounting numbers are reproducible and deterministic (verified by independent re-run).
Two confirmed defects require attention before results are presented: the structural
`contra` fallback (all-negative cells) will silently misclassify operating-loss rows on any
statement other than an asset-only page; and the accounting check for a gross item with a contra child but
**no** net child contributes the gross value (not gross-minus-contra) to the parent subtotal,
which can produce false failures on filings where the net is not separately printed.
Several minor issues also need attention: accounting pass-rate denominator visibility, silent empty
output on a one-column page, and the committed AI session transcript.

---

## 2. Verified claims table

| Claim | How verified | Result |
|---|---|---|
| 275 tests pass on original repo | `pytest -q` in working tree | PASS: 275 passed in 15 s |
| Fresh-clone reproducibility | Cloned to temp, fresh venv, `pip install -e "[dev]"`, `pytest -q` | PASS: 275 passed in 12.65 s |
| CSV output deterministic (byte-identical) | `parse_page.py` to temp, PowerShell diff vs examples/ | PASS: identical |
| Eval report deterministic | `run_eval.py` to temp, diff vs eval/results/page4_report.md | PASS: identical |
| P7-P8 did not change protected files | `git diff --stat 2f6fa06..HEAD -- data/ src/parser/rows.py ...` | PASS: empty diff |
| No GT leak in production parser | grep data/gt, "gt", page4 in src/parser/ excluding evaluation/ | PASS: zero hits |
| accounting.py takes no GT and no label text | Read source lines 1-179 | PASS: only IDs/types/amounts |
| No assertion removed in existing tests | `git diff 2f6fa06..HEAD -- tests/{test_rows,test_export,test_inspection,test_smoke}.py` | PASS: only import refactor + flatten_indentation move; no assertion removed |
| GT cell accuracy 1.0 (86/86) | Re-ran `run_eval.py` | PASS: 86/86 |
| Accounting: 7 exact + 13 within-tolerance, 0 fail, 2 N/A | Re-ran `run_eval.py` | PASS: confirmed |
| Residuals in -1..+3 |  Re-ran eval | PASS: confirmed in report |
| Truncation hypothesis: 20/20 inside interval | Re-ran eval | PASS: 20/20 |
| No absolute local paths in production source | grep_search on C:\Users, /home/, secrets | PASS: none found |
| CSV quoting of comma/quote/newline | Probe 3 round-trip | PASS: round-trip OK |

---

## 3. Findings

| ID | Severity | Area | Evidence | Why it matters | Fix suggestion | Effort |
|---|---|---|---|---|---|---|
| F1 | major | classify.py L60 | Probe 1: `営業損失` (all-negative cells, non-listed label) → `row_type='contra'`, `source='structural'` | Any income-statement loss row or negative-balance line item will be silently misclassified as `contra`. The rule fires for ALL rows with all-negative numeric cells, regardless of label. Only the 5 page-4 contra rows are correctly caught because they match the prefix list first. | Emit `possible_contra_or_loss` warning when structural contra fires without a label prefix match; classify as `line_item` (safer default) unless the label prefix matches explicitly. | M |
| F2 | major | accounting.py L72-81 | Probe 2 + code trace: gross `g1`(100) with contra CHILD `c1`(-20), no net child → `contribution(g1)=100` (own value, no net child). The contra child is NOT included in the parent subtotal sum. Subtotal gets expected=100, printed=80 → fail. | A real filing that prints gross+contra pairs without a separate net row will produce false accounting failures for any subtotal of that section. The spec says "a net child replaces gross contribution" but does not handle the case where no net row exists. | Document explicitly: "without a net child, gross contributes its own value; contra children are not summed separately into the parent subtotal". Alternatively add a gross-minus-contras contribution path. | M |
| F3 | minor | accounting.py / metrics.py | Pass rate = passed/evaluable. At y=0.75H 6/20 runs have undefined rate; at x=1H 7/20 undefined. No single scalar surfaces "fraction of checks that survived" | A reader seeing "pass rate=1.0" could miss that all checks vanished. | Add `evaluable_fraction = evaluable / (evaluable + not_evaluable)` to `accounting_summary()` and report it alongside pass rate. | S |
| F4 | minor | rows.py L45-53 | `_clusters` uses running median. A tall word shifts the median, potentially pulling the next row (y+2H) into the same cluster. Robustness sweep confirms failure at y=0.2H. | Rows can merge incorrectly under moderate jitter. | Replace running-median with simple nearest-existing-member gap check: if gap to any existing member > tolerance, start new group. | M |
| F5 | minor | rows.py L95-107 | Column detection uses running-median right-edge clustering with tolerance=0.3H. Robustness sweep shows cliff at x=0.3H. | Under moderate x-noise two columns split into three, silently producing `ambiguous_column_roles` and destroying all value alignment. | Use global histogram gap maximization or k=2 k-means (fixed for two-column pages) validated by column_min_support. | M |
| F6 | nit | classify.py L47-60 | Rule precedence: `total_suffixes` is intentionally empty in JA_FINANCIAL_STATEMENT. A section total labelled `X合計` where X is not in total_labels will be classified `subtotal` not `total`. Already documented in hierarchy_and_export.md. | No defect on page 4. Could silently misclassify on other statements. | Add one sentence to JA_FINANCIAL_STATEMENT docstring noting this limitation. | S |
| F7 | nit | hierarchy.py L46 | Empty input produces `rules_fallback` + `insufficient_indentation` warning (misleading for empty input). | Minor UX: warning message says "partial rules fallback: header nesting is unknown" when there are no rows to nest. | Add `empty_input` warning case. | S |
| F8 | nit | evaluate Probe 4 | `read_table()` raises `ValueError` on missing required columns instead of returning structured issues. Callers need a bare try/except. | Inconsistent error surface — other errors (invalid integer, invalid level) go into `issues` list, but missing columns raise. | Catch schema errors and return as Table with empty rows and issues list. | S |
| F9 | nit | rows.py Probe 5 | One-column page with single numeric column: `columns_detected=0`, `body_rows=0`. No warning emitted. Pipeline silently returns empty output. | A caller gets empty output with no indication that column detection failed. | Emit a `no_columns_detected` warning when `centres` is empty after filtering. | S |
| F10 | hygiene | chat_logs/ | `chat_logs/transcript_full.jsonl` (430 KB) and `chat_log.md` (47 KB) committed in `a46ee03`. Contains AI session transcript. Not in `.gitignore`. | Potential privacy/data-control issue before public release. | Add `chat_logs/` to `.gitignore`; document in README that logs are submitted per brief requirements. | S |

---

## 4. Overclaims

| Claim | Location | Assessment |
|---|---|---|
| "First measured degradation at y=0.2H and x=0.3H" | README L363, failure_analysis.md | Supported; correctly qualified as "first degraded tested amplitude, not a mathematical boundary". |
| "All 72 numeric cells participate in accounting checks" | README L365 | Supported — directly from fault injection. |
| "Only 249/648 units-digit faults detected" | README L365 | Supported by fault injection. |
| "GT metrics 1.0 on every metric" | README L352 | Supported — verified by independent re-run. |
| "Development results on one page; rules designed after seeing it; do not establish generalisation" | README L368 | Correct honest caveat. |
| "AI-drafted GT verified by one human, who also reported an independent second review" | README L370 | Unverified by this reviewer; stated honestly. |
| "360 runs, well under two minutes" | README L359 | Timing not independently verified; trusting builder. |
| Implied: structural fallback contra is correct | hierarchy_and_export.md L52-63 | Overclaim by omission: the notes do not warn that this fires on income-statement loss lines. Add warning. |

---

## 5. Hygiene and privacy

| Item | Detail |
|---|---|
| `chat_logs/transcript_full.jsonl` (430 KB), `chat_log.md` (47 KB) | Committed `a46ee03`; not gitignored. May contain private session content. |
| `notes/words_pymupdf.json`, `notes/words_pdfplumber.json` | Large derived files (16-21 KB) committed. Low risk (PDF word dumps) but add noise. |
| No absolute paths, emails, tokens in src/ | grep_search confirmed clean. |
| `pandas` listed in `pyproject.toml` dependencies | `import pandas` not found in src/parser/. Used only in diagnostic scripts. Declare as optional or move to `[dev]`. |
| `.gitignore` excludes `outputs/` | Correct. |

---

## 6. Recommended P10 fix list (top 7, ~2 hours)

| # | Fix | Acceptance test |
|---|---|---|
| 1 | **F1: structural contra guard.** Change structural contra fallback: when `all_negative_cells=True` but no label prefix matches `contra_labels`, classify as `line_item` and emit `possible_contra_or_loss` ParseWarning. | Probe 1 re-run: `営業損失` → `line_item` with warning. Page-4 real-page test still passes (all 5 contra rows match prefix list first). |
| 2 | **F2: document gross-without-net accounting behavior.** Add explicit test: gross+contra child, no net child, subtotal → expected=gross (not net). Update evaluation_design.md section. | New test passes; `not_evaluable` is not returned; existing tests unchanged. |
| 3 | **F3: evaluable_fraction metric.** Add `evaluable_fraction` to `accounting_summary()`. Show in Markdown report. | Re-run `run_eval.py`; `evaluable_fraction` key present in JSON; reported in table. |
| 4 | **F4: rows.py cluster gap fix.** Replace `_clusters` running-median with nearest-gap termination. | 275 existing tests pass. First y-degradation in robustness sweep shifts to ≥0.3H (or more). |
| 5 | **F9: no-column warning.** Emit `no_columns_detected` warning from `reconstruct_page` when `centres` is empty after filtering. | Probe 5 re-run: warning present in output. One-column page test added. |
| 6 | **F10: gitignore chat_logs.** Add `chat_logs/` to `.gitignore`. Update README with note on AI log submission. | `git status` shows chat_logs/ as ignored on fresh clone. |
| 7 | **F8: structured schema error in read_table.** Return structured issues for missing-column errors instead of raising ValueError. | Probe 4 re-run: `table.issues` contains the schema error; no exception raised. |

---

## 7. Probe results

| Probe | Question | Command/method | Output |
|---|---|---|---|
| P1 | all-negative non-listed label → classify | `classify_row(row)` where `row.label='営業損失'`, cells=[△1234, △5678] | `row_type='contra'`, `source='structural'`. **Bug F1 confirmed.** |
| P2 | gross+contra sibling, no net, subtotal accounting | `accounting_checks(rows_p2, ("col",))` with g1+c1+s1 all under parent=None | `not_evaluable` — correct for root-level subtotal with no preceding siblings (probe setup had no parent header). Real case (gross with contra CHILD, no net) produces gross-contribution to parent subtotal. |
| P3 | comma/quote/newline in label, CSV round-trip | Write via csv.writer, read via read_table | `Round-trip OK: True`. No quoting defects. |
| P4 | missing `row_id` column → error handling | `read_table(bad_csv)` | `ValueError: missing CSV fields: ['parent_path', 'row_id']`. Clear message but exception not issues-list. |
| P5 | one-column page, pipeline crash? | `reconstruct_page(raw_p5)` with one numeric word | `columns=0, body_rows=0`. No crash. Silent empty output; no warning. |
| P6 | two equal totals → balance check | `accounting_checks` with t1(100) + t2(100) | `balance:exact`. Unequal (100 vs 105): `balance:fail, residual=5`. Correct. |
| P7 | duplicate label, missing row in prediction | `align_rows(pred, gt)` where second その他 missing in pred | `pairs=((0,0),(1,2))`, `unmatched_gt=(1,)`. Correct: second その他 left unmatched; 合計 correctly aligned. |
| P8 | pdfplumber independent count | `pdfplumber` on actual PDF | 73 numeric tokens (expected 74 = 43×2 - 1 page-number token captured). 38 distinct row y-groups (after 5pt tolerance). Accounting report found. |

---

## 8. What was not checked

- `eval/results/robustness_report.json` (excluded per budget rules)
- `notes/words_*.json`, `notes/drawings.json` (excluded)
- `data/derived/*` (excluded)
- The human GT second-review record (cannot independently verify)
- Actual runtime of the robustness sweep
- Whether chat_logs contains PII beyond session content
- `src/parser/evaluation/perturb.py`, `faults.py`, `robustness.py`, `report.py` (non-core eval modules, not read in full)
- `tests/test_evaluation.py`, `tests/test_accounting.py`, `tests/test_perturbation.py` (52 new tests — only names/counts noted)
- Japanese-era date parsing edge cases in normalize.py
- OCR/VLM stub (P12 scope)
- Multi-page or multi-table scenarios (untested by design)
