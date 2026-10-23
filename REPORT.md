# DRAFT — Japanese balance-sheet extraction

## 1. Problem and assumptions

The task is to convert a born-digital Japanese consolidated balance sheet into a flat CSV and hierarchical JSON, retaining amounts in printed 千円 units. (PROJECT_BRIEF.md)
The promised CSV fields are label, parent, level, row_type and previous/current values; exports also retain identifiers, paths and raw strings. (PROJECT_BRIEF.md; README.md)

This is a development result on one supplied page, with rules written after seeing it, not evidence of generalisation. (eval/results/page4_report.md)
GPT 6.1 Sol transcribed the page image; the owner checked it row by row, and a later Claude conversation gave a second AI reading. These roles are owner-supplied, not independently verifiable from the repo. (workstamp.md, user-supplied attribution)
The subsequent PDF text-layer cross-check agreed on 74/74 cells, including nil marks and signed zero. (notes/p2_report.md)

## 2. Approach

PyMuPDF extracts words and geometry into backend-neutral records; reconstruction groups rows, repeated numeric right edges and indentation, then classification, hierarchy, metadata and deterministic export follow. (README.md)
Distances scale with median word height rather than fixed coordinates; Japanese label patterns live separately in a replaceable RuleSet. (README.md)
An indentation stack assigns parents; without useful indentation, the warned fallback only partially reconstructs nesting. (notes/hierarchy_and_export.md)
The backend interface permits a later OCR/VLM reader, but that reader is not implemented. (README.md)

## 3. What “correct” means

The evaluator reads exported files independently of parser objects, while accounting receives only predicted IDs, types, amounts and raw strings, without labels or GT. (notes/evaluation_design.md)

Alignment comes before scoring: order-preserving dynamic programming handles missing, extra and repeated labels, combining label similarity and matching-value fraction with equal weights and a default threshold of 0.5. (notes/evaluation_design.md)
Ties are deterministic, but indistinguishable repeated rows remain ambiguous; aligned-row F1 alone cannot prove semantic correctness. (notes/evaluation_design.md)

**Cell correctness:** exact integer/null equality, with all GT cells and nonempty-raw printed cells reported separately; missing GT rows count wrong, and nil differs from zero. (notes/evaluation_design.md)
Raw-string and exact/normalized-label accuracy separately expose representation errors. (notes/evaluation_design.md)

**Structural correctness:** precision is aligned/predicted rows, recall is aligned/GT rows, and F1 combines them. (notes/evaluation_design.md)
Type, level, parent path, ancestor-chain Jaccard and optional column roles/dates are scored separately; parent correctness maps identities through alignment, avoiding duplicate-label confusion. (notes/evaluation_design.md)
A fully correct row requires label, values, type, mapped parent and level to agree; undefined denominators are N/A. (notes/evaluation_design.md)

**Accounting consistency:** subtotals/totals sum preceding sibling contributions; a net child replaces gross, otherwise gross includes contra children, and headers contribute their subtotal. (notes/evaluation_design.md)
Net checks add gross and negative contras; null contributes zero only for a raw nil marker, while invalid inputs make checks unevaluable. (notes/evaluation_design.md)

Residual means printed minus expected; default tolerance is max(1,n), with n addends. (notes/evaluation_design.md)
Under an exact underlying identity, truncation errors bound the absolute residual below n+1, so its integer value is at most n; nearest rounding is also covered. This is a conservative allowance, not an error detector guarantee. (notes/evaluation_design.md)
Pass rate is (exact+within_tolerance)/(exact+within_tolerance+fail); evaluable_fraction is evaluable/applicable checks, excluding not_applicable. (notes/evaluation_design.md)
Both matter because checks can disappear while the remaining pass rate looks healthy. (notes/failure_analysis.md)

The separate interval [−negative-addend count, positive-addend count−1] is a **truncation hypothesis diagnostic**, never the default pass rule; signed/zero edge cases prevent treating it as universal. (notes/evaluation_design.md)
The actual filing policy remains unconfirmed. (notes/evaluation_design.md)

## 4. Results on the supplied page

| Metric | Correct / denominator |
|---|---|
| All value cells; raw strings | 86/86 each (eval/results/page4_report.md) |
| Printed cells, including nil | 74/74 (eval/results/page4_report.md) |
| Exact labels; types; levels; parents; fully correct rows | 43/43 each (eval/results/page4_report.md) |
| Row precision; recall; F1 | 43/43; 43/43; 86/86 (eval/results/page4_report.md) |
| Column roles; dates | 2/2 each (eval/results/page4_report.md) |

Accounting has seven exact and thirteen within-tolerance checks, no failures, and two balance checks not applicable because only one total is present. (eval/results/page4_report.md)
Pass rate and evaluable_fraction are both 1.000000. (eval/results/page4_report.md)
Residuals range from −1 to +3 千円; truncation consistency is 20/20, which does not establish the filing's policy. (eval/results/page4_report.md; notes/evaluation_design.md)

## 5. Robustness and failure analysis

Measured sweeps perturb word geometry, not the PDF: twenty seeds per amplitude/axis, with 360 runs; H denotes median word height. (notes/failure_analysis.md)
Selected P8→P10 results below remain unchanged in P10b. (notes/failure_analysis.md)

| Test and metric | Before → after, mean/minimum |
|---|---|
| x=0.3H, cell accuracy | .3331/.0000 → .9360/.8488 (notes/failure_analysis.md) |
| y=0.3H, cell accuracy | .5994/.0000 → .8890/.0000 (notes/failure_analysis.md) |
| x=0.75H, row F1 | .9500/.8605 → .6503/.5581 (notes/failure_analysis.md) |
| x=0.75H, parent accuracy | .5698/.3721 → .2977/.0698 (notes/failure_analysis.md) |

Gap clustering improved cells but regressed structure at higher noise; success cannot be claimed from cell accuracy alone. (notes/failure_analysis.md)
At x=0.3H all seeds retain correct column roles, yet the cell-assignment gate affects ninety row-seed cases; rejected numbers contaminate labels. (notes/failure_analysis.md)
The y=0.2H seed-11 lease-depreciation split remains. (notes/failure_analysis.md)
A pitch-based candidate was rejected at a test preserving that known failure; no threshold change or candidate-wide robustness success was retained. (notes/p10_audit.md)

Flattening indentation preserves values but lowers parent accuracy to 38/43 and fully correct rows to 14/43; dropping rules, translation, scaling and shuffling preserve the measured GT scores. (notes/failure_analysis.md)

Fault injection covers 72/72 numeric cells and exhaustively mutates digits, signs and nil blanks. (eval/results/robustness_report.md)

| Digit position | Detected / injected |
|---|---|
| Units | 249/648 (eval/results/robustness_report.md) |
| Tens | 621/639 (eval/results/robustness_report.md) |
| All higher-than-units digits combined | 3007/3025 (eval/results/robustness_report.md) |

A small last-digit error can hide within a many-addend tolerance; arithmetic also cannot distinguish signed-zero/nil no-ops. (notes/failure_analysis.md)

## 6. Limitations and next steps

Scans, wrapped/multi-page or multiple tables, other statements and languages remain expected challenges, not tested results. (notes/failure_analysis.md)
Proposed work, not measured capability: add OCR/VLM behind the existing interface, then validate each new input class on a held-out set. (PROJECT_BRIEF.md; notes/failure_analysis.md)
To address the documented indentation limitation, I would compare learned layout models; to scale beyond the current file evaluator, I would annotate many PDFs, freeze document-level development/held-out splits, and report pooled counts plus per-document averages. These are proposals, not implemented results. (README.md; notes/evaluation_design.md; notes/failure_analysis.md: motivations)

## 7. How I used AI tools

The following attribution is **owner-supplied**, not independently verifiable from repo records. (workstamp.md, user-supplied attribution)
Claude on the web, using a separate account, drafted the implementation plan and prompts; a later Claude conversation provided the second AI GT reading and reviewed prompts and results. (workstamp.md, user-supplied attribution)
Claude Opus 4.6 handled P0–P1; GPT 6.1 Sol in Codex handled P2–P8 and P10b–P13. (workstamp.md, user-supplied attribution)

The P9 reviewer, Claude Sonnet 4.6, differed from the builder model; P10a fixes were applied by a third model, Gemini Flash 3.8, with that work recorded in commits 5565491 and d51c47f. P10a is the fix stage labelled P10 in the experiment comparisons. (workstamp.md, user-supplied attribution)
GPT 6.1 Sol then audited the fixes in P10b, reusing the original builder model. This has weaker independence than a human audit; it is not a claim of full independence. (workstamp.md, user-supplied attribution)
The handoff file records plans, commits, decisions and usage-limit cutoffs across sessions. (workstamp.md)

Time spent: about two days of elapsed time (Wed 21 to Fri 23 Oct 2026), mostly agent runtime plus my own planning, prompt drafting and manual verification of the ground truth. I did not keep a precise log, so this is an estimate.

<!-- drafted by agent from repo facts; owner may edit -->
I used accounting checks to expose small rounding-sized differences between printed totals and component sums that exact agreement with transcribed cells alone cannot explain. (eval/results/page4_report.md; notes/evaluation_design.md)
I used jitter sweeps to expose real failures, including the P10 fixes' regressions in row F1 and parent accuracy at higher noise. (notes/failure_analysis.md)
I retained the documented rejection of the pitch-threshold attempt and the remaining seed-11 row split as limitations. (notes/p10_audit.md; notes/failure_analysis.md)
I measured everything on one page, with rules written after seeing it, so these results do not establish generalisation. (REPORT.md, sections 1 and 5)
My next step would be held-out pages and an OCR/VLM backend, evaluated as new work rather than assumed capability. (notes/failure_analysis.md; PROJECT_BRIEF.md)

## 8. Reproduce

With the virtual environment activated, run these README commands from the repository root; committed examples are the evaluation inputs. (README.md)

```bash
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf --page 1 --out-dir outputs
python eval/run_eval.py --pred examples/balance_sheet_after_correction_p1.csv --pred-json examples/balance_sheet_after_correction_p1.json --gt data/gt/page4.csv --gt-meta data/gt/page4_meta.json
python eval/run_robustness.py
```

Command source: (README.md).
