# Japanese balance-sheet extraction

A born-digital Japanese PDF parser produces flat CSV and hierarchical JSON.
This report separates the original human-verified development page from a small,
provisional additional-page benchmark. It reports failures as well as successful
extraction. Start with the reproduction commands below and the detailed results.

## 1. Problem and scope

The original task is a consolidated balance-sheet page in 千円, with comparative
periods, repeated labels, nil marks, triangular negatives and indentation-based
hierarchy. Amounts stay in printed units; JSON includes unit metadata. The backend
interface isolates PDF reading for a possible future OCR/VLM implementation.
(PROJECT_BRIEF.md; README.md)

The original rules were written after seeing the supplied page. Its image-based
GT was transcribed by GPT 6.1 Sol, checked row by row by the owner and given a
second AI reading by Claude; that attribution is owner-supplied. A PDF text-layer
cross-check agreed on74/74 printed cells. (workstamp.md; notes/p2_report.md)

## 2. Approach and changes

PyMuPDF words and ruling evidence feed relative row/column clustering, row typing,
indentation-based parents, metadata and deterministic exports. Language rules are
separate from geometry. CSV retains IDs, parents, raw strings and normalized values;
JSON nests the same rows. (README.md; notes/hierarchy_and_export.md)

Period headings now need a complete, unique date band in the detected numeric
column regions before supported body values. Footer dates and dated body labels
cannot move the header past those values. Missing or ambiguous dates retain the
first-value-row fallback with a warning; leading label-only sections can be lost
in that fallback. Multiple tables and repeated numeric notes remain limitations.
(notes/p14_changes.md; tests/test_p14.py)

Recognized numeric tokens can recover to their nearest column within twice the
clustering tolerance, bounded by neighbouring midpoints. Other text keeps the
strict assignment gate. Review flags expose invalid amounts, incomplete cells,
unassigned numbers and orphan amount rows; ambiguous roles and weak indentation
also warn. Warnings are visible in JSON and the CLI, not confidence probabilities.
No body/columns produces CLI exit2; usable output with warnings exits0.
(notes/p14_changes.md)

## 3. What “correct” means

CSV alignment uses order-preserving dynamic programming with equal label-similarity
and matching-value contributions and threshold0.5. Missing/extra rows remain in
denominators and mismatch lists. Indistinguishable repeated rows can still align
ambiguously. (notes/evaluation_design.md)

**Cells:** compare exact integer/null values against all GT cells and, separately,
printed cells with nonempty raw strings. Raw representations and exact/normalized
labels are separate metrics. Unknown amounts are not silently zero.
(notes/evaluation_design.md)

**Structure:** row precision/recall/F1, types, depth, mapped parents, ancestor paths
and fully correct rows are separate. A fully correct CSV row requires the exact
label, values, type, mapped parent and depth; raw equality is reported separately.
Undefined denominators are N/A. (notes/evaluation_design.md)

**JSON:** standalone evaluation validates schema/types and value records, walks
actual nesting to derive depth and parents, and detects duplicate/missing IDs,
malformed children, inconsistent declarations and absent nodes. JSON/CSV consistency
joins by identity; JSON/GT accuracy uses its own label/value alignment. Declared
levels never substitute for nesting. Omitted JSON is explicitly not_supplied;
empty/malformed JSON fails validation even with a perfect CSV. Schema-invalid JSON
writes a diagnostic report and exits2. Data mismatches remain in the report.
(notes/p14_changes.md; tests/test_p14.py)

**Accounting:** predicted subtotals, net amounts and totals are checked without GT
or labels. Default tolerance is max(1,n) for n addends: if an underlying identity
holds, truncation bounds the integer residual by n, and nearest rounding is also
covered. The tighter signed truncation interval is only an unconfirmed hypothesis
diagnostic. A raw nil mark permits a null contribution; invalid amounts make a
check unevaluable. Report pass rate alongside evaluable/applicable coverage because
broken structure can remove checks. Arithmetic consistency is not extraction truth.
(notes/evaluation_design.md)

## 4. Supplied-page development results

| Metric | Result |
|---|---|
| CSV all cells / printed cells |86/86;74/74 |
| Exact labels, parents, fully correct rows |43/43 each |
| JSON/GT fully correct rows; JSON/CSV |43/43; consistent |
| Accounting |20/20 evaluable:7 exact,13 within tolerance;2 not applicable |

Source: eval/results/page4_report.json. Fresh CSV/JSON match committed examples
byte for byte. These results describe the supplied development page, not a
held-out measurement. (notes/p14_changes.md)

## 5. Additional pages and baseline

Five official filings were split by issuer before acquisition: Nintendo/Capcom
for development; Sega Sammy/Square Enix/Konami held out. Original parser3e14d24
and candidate33025ad were frozen before held-out predictions. No parser tuning
followed those results. All new pages use 百万円. Four share similar templates,
and all issuers are in one industry. (benchmarks/manifest.json)

Annotations were drafted from rendered pages before predictions by the coding
agent, not a separate reviewer. They are **AI-only and provisional**. Four
transcription mistakes were corrected after mismatches prompted enlarged-image
review; initial drafts and results are preserved. That adjudication was not blind.
Row-type ontology disagreements remain. (benchmarks/README.md)

| Scope / engine | Cells | Fully correct rows |
|---|---|---|
| New development, either parser |118/118|50/59|
| Held out, either parser |262/262|129/131|
| Held out, pdfplumber |250/262|N/A: no hierarchy/types|

Source: eval/results/benchmark/report.json. Candidate/original labels and parents
are131/131 held out; per-page cell means are1.0000 for both. Pdfplumber omits two
leading headers per held-out page. All selected pages and mismatches remain in the
reports; success on this narrow provisional sample is not broad generalisation.

The baseline uses fixed pdfplumber text-grid settings and a format/normalization
adapter, without parser coordinates or GT. Its chronology assumes left-to-right
ordering. Timings include PDF opening through in-memory serialization, excluding
startup, annotations and evaluation: one warmup, five repetitions on the same
Windows/Python3.14.0 machine. (benchmarks/README.md; eval/results/benchmark/report.json)

| Page | Candidate median/IQR ms | pdfplumber median/IQR ms |
|---|---:|---:|
| Supplied |16.97/4.27|102.49/2.76|
| Sega Sammy |24.55/3.01|180.96/19.66|
| Square Enix |13.70/1.02|424.13/10.69|
| Konami |41.78/0.28|101.46/4.17|

Source: eval/results/benchmark/report.json. Original-parser medians on these
held-out pages were24.91,11.77,40.67ms respectively; the candidate is not uniformly
faster. Small differences, fixed engine order and warm caches preclude a speedup
claim between parser revisions. Baseline structural capability is explicitly unequal.

## 6. Robustness and remaining failures

The supplied-page sweep retains20 seeds per condition and360 geometry runs.
At x=.3H, mean/minimum cell accuracy improves .9360/.8488→1.0000/1.0000;
mean parent accuracy improves .9640→.9977, while accounting pass rate drops
1.0000→.9950 as coverage rises .7650→1.0000. (eval/results/p14/comparison.md)

There are regressions: at y=.5H, mean cells .3866→.3843, row F1 .7975→.7906,
parents .8581→.7535. At y=.3H cell mean remains .8890, minimum0. The seed-11
row split remains. The earlier pitch-threshold attempt was rejected, not a success.
The historical P10 high-noise structural regressions are still documented.
(eval/results/p14/comparison.md; notes/failure_analysis.md; notes/p10_audit.md)

Ablations still expose weak indentation: parent38/43 and fully correct14/43.
Fault detection is unchanged:3256/3673 digit substitutions,71/72 sign flips and
71/72 nil/blank faults. Only249/648 units-digit faults are detected; the tolerance
has not been tightened to inflate detection. (eval/results/p14/robustness_report.json)

Scanned pages, OCR/VLM, training/GPU serving, multi-page assembly and learned
hierarchy remain unimplemented. Next evaluation needs independently reviewed
annotations and a broader held-out issuer/layout set. If these outcomes guide
future fixes, this held-out set must become development data. (benchmarks/README.md)

## 7. AI use and maintenance

Owner-supplied attribution: Claude web helped planning/prompts; Claude Opus4.6
handled P0–P1, GPT6.1 Sol P2–P8/P10b–P13, Claude Sonnet4.6 reviewed P9,
and Gemini Flash3.8 applied P10a fixes. The builder model's P10b audit is weaker
independence than a human audit. P14 implementation and provisional annotations
were agent-assisted in Codex; no independent reviewer is claimed. (workstamp.md)

The handoff tracks interrupted work and immutable baselines. Log export now defaults
to a separate directory, refuses implicit replacement and backs up explicit
replacement. Existing logs are preserved; a visible-message supplement documents
its cutoff and excludes private reasoning/platform instructions. CI runs tests and
Ruff without benchmark downloads. (chat_logs/README.md; notes/p14_changes.md)

## 8. Reproduce

Install in the README's Windows/Python3.14 environment, set PYTHONIOENCODING=utf-8,
and run from the repository root. New benchmark downloads are explicit and hash-checked.

```powershell
python -m pytest
python -m ruff check src scripts tests eval
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf --page 1 --out-dir outputs
python eval/run_eval.py --pred examples/balance_sheet_after_correction_p1.csv --pred-json examples/balance_sheet_after_correction_p1.json --gt data/gt/page4.csv --gt-meta data/gt/page4_meta.json
python eval/run_robustness.py --out-dir eval/results/p14
python scripts/run_benchmark.py --download --render
```

Source: README.md. See benchmarks/README.md for the verified-TLS Windows download
fallback, annotation review and timing boundaries. No OCR/backend deployment is claimed.
