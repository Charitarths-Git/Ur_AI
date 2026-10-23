# Evaluation design: correctness and consistency on one development page

## Scope and independence

The primary API `evaluate_files(pred_csv, gt_csv, pred_json=None, gt_meta=None,
threshold=0.5)` reads exported files, not ParsedPage objects. CSV uses the P6
schema and utf-8-sig; GT uses its verified schema. A different system emitting
that schema can be evaluated. Independent EvalRow/Table records preserve raw
strings, integer/null values, IDs, types and paths. Prediction parent IDs are
explicit; missing parent IDs are not inferred from GT or credited using labels.
GT has no parent-ID column, so its IDs are derived from preceding printed paths.
When identical full ancestor paths repeat, the latest preceding match is used;
such indistinguishable GT structure needs explicit IDs to remove ambiguity.

The parser never reads GT. Accounting receives a separate AccountRow with **no
label field**: ID, parent ID, type, amount tuple and raw tuple only. It receives
no GT. Robustness writes each pipeline result to temporary CSV/JSON files and
then invokes the same file evaluator, with no privileged object-based scoring.
The PDF is read once per robustness run; only RawPage objects are perturbed.

All output ordering, seeds and tie rules are fixed. Reports contain no timestamps;
source names are basenames. Generated report text is UTF-8. P7–P8 left existing parser code,
GT, raw PDF, examples and dependency manifests unchanged. P10 later fixed the
reviewed parser behavior; P10b provided an audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit. Protected GT/raw/examples
remain unchanged. Existing test
transform helpers were moved into evaluation.perturb without weakening assertions.

## Ordered alignment

For prediction i and GT j, compute:

`s(i,j) = 0.5 L(i,j) + 0.5 V(i,j)`

L is 1 when label_key values match, otherwise Python SequenceMatcher's character
ratio on those keys (`autojunk=False`). V is the fraction of GT value roles
whose integer/null values match and are valid on both sides. Missing prediction
roles are wrong even for expected empty/null header cells. Nil and zero differ.
Invalid missing values are not credited as legitimate nulls. With no GT value
columns V is 0. Similarities use no parent, path, type or GT-derived parser rules.

A suffix dynamic program maximizes summed similarity over monotone pairs with
free gaps. A pair is allowed only when s>=threshold (default 0.5). Secondary
objective is pair count. Remaining ties prefer match, skip prediction, skip GT;
suffix traceback therefore selects earliest indistinguishable current pairs.
Scores are compared rounded to twelve decimal places for stable ties. Complexity
is O(prediction rows × GT rows) in time and memory. Repeated label-ratio work is
cached; no experimental GT tuning is done. Tests cover duplicates with missing
and extra rows and exact-information ties.

Identical repeated labels and values can be inherently ambiguous. The alignment
is a reproducible matching policy, not proof of semantic identity. Because a
pair with identical values can reach 0.5 despite a completely different label,
aligned-row F1 must be read alongside cell, label and structure metrics.

## Metrics: formulas and denominators

Let G be GT row count, P prediction row count, A aligned pair count, C GT value
role count, and D the count of GT cells whose raw string is nonempty. Unaligned
GT rows contribute zero to every GT-based numerator, including empty header
cells. Extra prediction rows affect precision/F1, not GT-cell denominators.

| Metric | Numerator / denominator |
|---|---|
| cell_accuracy_all | Correct integer/null cells / G×C |
| cell_accuracy_printed | Correct integer/null cells restricted to nonempty GT raw / D |
| raw_accuracy | Exact raw strings / G×C |
| label_exact | Identical printed labels / G |
| label_key | Equal comparison keys / G |
| row_precision | A / P |
| row_recall | A / G |
| row_f1 | 2A / (P+G), equivalent to harmonic mean where defined |
| fully_correct_rows | Rows with exact label, every value, type, mapped parent and level correct / G |
| row_type | Correct types / G; also report GT→prediction confusion counts, including missing rows |
| level | Equal ancestor-count levels / G |
| parent | Correct parent identity after mapping predicted parent through alignment / G |
| parent_path | Exact printed ancestor-path strings / G |
| ancestor_jaccard | Sum of mapped ancestor-set intersection/union ratios / G |
| column_roles | Correct role at each unique expected column index / max(expected,predicted column count) |
| column_periods | Correct ISO date at each unique expected column index / same column denominator |

Both-root parent links count as correct. A missing, unaligned or incorrect
parent does not. Ancestor sets map through alignment; unaligned/invalid IDs use
nonmatching sentinels, and cycles terminate safely. Two empty ancestor sets
have Jaccard 1. Parent identity can be wrong even if the printed parent labels
and parent_path strings look identical; duplicate-parent tests demonstrate this.

Column metrics are optional and N/A without both predicted JSON and GT metadata.
The supplied GT's expected order is previous_year at index 0 and current_year
at index 1, with dates from period_end_dates. This metadata contract assumes the
provided two-year GT layout; other GT column metadata needs an explicit extension.
Wrong roles and wrong dates are scored separately at their expected indices.
Extra/duplicate prediction indices increase the denominator or fail uniqueness.

Zero denominators are N/A (`null` score), never silently 1. Empty prediction
against nonempty GT has zero recall/F1/cell accuracy and undefined precision.
Empty GT has undefined GT-row/cell metrics. The report gives every metric's
numerator, denominator, formula description and score; all mismatches list row
IDs, printed label and field, plus a reason for missing-role/invalid-value cases.
Exact label differences and raw formatting differences stay separate from key
and integer equality. Fully-correct rows follow the requested fields; raw strings
and parent_path also have their own metrics rather than silently entering it.

`aggregate_reports` pools numerator/denominator counts for micro averages and
averages defined page scores for macro averages, reporting defined/total pages.
It also pools accounting pass, evaluable_fraction and truncation-diagnostic counts
when present. Coverage pools evaluable/applicable counts, with N/A for zero
applicable checks.
Tests combine the same page twice. **For one page, defined micro and macro scores
coincide.** This does not turn one page into an independent validation set.

On the real page: G=P=A=43, C=2, all-cell denominator86, printed-cell denominator74.
The 12 empty header cells are included only in the all-cell denominator; the
two printed nil cells are included among printed cells and remain distinct from 0.

## Label-free accounting

Rebuild ordered sibling groups from row_id/parent_row_id. For a node's contribution:

1. If it has exactly one net child, use that child's amount.
2. Without a net child, use its own amount plus all contra-child amounts. Nil
   contributes zero only for a raw nil marker; any invalid required amount
   makes this contribution not_evaluable. Dependencies include gross and contras.
3. Otherwise for a header, use its exactly one subtotal child's amount.
4. Missing or ambiguous contributions are not_evaluable, never guessed by summing leaves.

Each subtotal/total sums contributions of siblings preceding it under the same
parent. Net checks use gross own amount plus all contra-child amounts (at least
one contra is required). Thus gross and depreciation are not double-counted in
a section sum. Header subtotal contributions feed parent totals. If exactly two
total rows exist, a separate balance check compares them; with one total here,
each column's balance check is not_applicable.

Null contributes zero only if its raw parses as a standalone nil dash marker.
Empty or invalid/unparseable raw null is not_evaluable. A numeric zero, including
printed negative zero, is a valid zero. Column roles/printed units are retained;
no unit multiplication or GT values are available to accounting.

Checks expose ID, kind, target row ID, column, number of addends n, expected,
printed, residual=`printed−expected`, tolerance, status and dependency cells.
Statuses: exact, within_tolerance, fail, not_evaluable, not_applicable. A missing
parent or required net/contra contribution cannot yield a passing guessed zero.
Accounting pass rate is `(exact+within_tolerance)/(exact+within_tolerance+fail)`.
`evaluable_fraction = evaluable / applicable`, where applicable excludes only
not_applicable. Thus zero evaluable among positive applicable checks is coverage0
with pass-rate N/A; no applicable checks makes both N/A. Page JSON accounting
and Markdown headlines show both. Geometry JSON/Markdown show their mean/minimum
over defined seeds, with defined/attempted-run counts retained. Ablations show
both values for each deterministic transformation.
Always show not_evaluable and N/A counts too: missing checks can inflate a rate
computed on the surviving checks. No evaluable checks means N/A, not success.

## Default tolerance derivation

Assume the underlying identity is true and each printed term and printed sum is
independently rounded/truncated to an integer of its printed unit. Default
`addend_tolerance(n)=max(1,n)` is replaceable through a callable ToleranceModel.

- Toward-zero truncation gives each figure an error strictly between −1 and +1
  printed units. Subtracting the sum of n such errors from the total's error
  gives absolute residual strictly less than n+1. An integer residual therefore
  has absolute value at most n.
- Nearest-integer rounding gives absolute residual at most (n+1)/2, which is
  <=n for n>=1. Default n therefore conservatively covers both policies.

The tolerance is in printed units: on this page one unit is 千円. n includes
nil-zero addends that still occupy a contributing row. Checks with no usable
addends are not_evaluable; they do not receive an automatic exact zero result.

## Truncation hypothesis diagnostic

Separately compute the requested integer interval
`[−number_of_negative_addends, number_of_positive_addends−1]` and whether residual
lies inside it. Counts use signs of effective printed addends; zeros count as
neither positive nor negative. This flag **never changes status or tolerance**.

On this page all 20 evaluable residuals lie in their intervals (20/20); their
range is −1..+3 千円, confirming the supplied page-specific hand check. This is
consistent with, but does not prove, an individually truncated filing. The human
must verify the actual rounding policy; no external convention is assumed.

There is a mathematical limitation to treating the supplied interval as a
universal assertion: an exact negative-only synthetic sum has residual 0 but
the literal interval ends at −1. All-zero addends give an empty interval, and
printed zero may hide an unprinted fraction. Tests explicitly retain the
requested formula and show this limitation. The conservative tolerance proof
above is independent of it. More sign/total information would be needed for a
universal toward-zero interval; this phase does not silently substitute one.

## Perturbation experiment design

The existing P4/P5 test helpers now live in evaluation.perturb: translate, scale,
shuffle, bounded two-axis jitter, flatten_indentation. Added drop_rules and
separate x/y jitter. Same seed gives identical RawPage output; input is immutable.
Jitter independently translates each word's bbox without resizing it. Rules are
not jittered; jitter runs also shuffle words/rules. Translate uses (−240,+375),
scales are 0.45/2.75; all distances scale through unchanged parser config.

Sweep amplitudes: 0,0.05,0.1,0.2,0.3,0.4,0.5,0.75,1.0 H on each axis, seeds0..19:
360 full pipeline/file-evaluator runs. All seeds retained; runtime well under two
minutes. For each amplitude show mean and worst cell accuracy, row F1, parent
accuracy and accounting rate, crashes and defined-run counts. Undefined accounting
rates are excluded from their mean with explicit counts. A parser crash would
count zero for GT sweep scores and remain visible as a crash, not disappear.

All six structural ablations include the complete metric/accounting report in
JSON. Only requested summaries are in Markdown. Seed records include mismatch
counts and up to 12 examples; this is deliberately sampled diagnostic detail,
while ordinary evaluation/ablation reports list every mismatch.

First degraded tested amplitude: y0.2 H and x0.3 H, consistent with the unchanged
row tolerance0.35 H and right-edge tolerance0.30 H under independent word shifts.
It is not a universal bound; see failure_analysis.md for measured seed examples.

## Exhaustive fault injection

Use only predicted numeric cells and label-free accounting records. Every decimal
digit position gets each different substitution, excluding a new leading zero
in multi-digit figures. Positions count from units=0. Each numeric cell also gets
one sign flip and one nil blank. There is no random sampling. The printed nil
cells and empty headers are not numeric fault targets. Full-width decimal glyphs
are supported; the supplied numeric body uses ordinary decimal digits.

Coverage is the fraction of numeric cells appearing in an applicable accounting
dependency. Also record how many appear in baseline-passing checks. A fault is
detected iff at least one check that passed before now has status fail. Other
outcomes are not relabeled as detections. Every undetected fault retains its
row/column, raw fault, effective value and impacted check n/residual/tolerance.
Numeric-zero sign flips and nil blanks remain in denominators as explicit no-ops.

Measured population:72 numeric cells, all covered;3673 digit substitutions and
72 each sign flips/nil blanks. Detection is3256/3673 for digits,71/72 for each
other type. Units249/648; higher3007/3025. Of419 undetected faults,417 numeric
changes remain inside tolerance and2 are numeric no-ops. A last-digit change
can hide inside a many-addend sum's tolerance; even18 tens-digit changes do here.
These are detector results on this page/these faults, not extraction accuracy.

## Evaluator validation and limitations

Tests cover perfect/incorrect cells, swapped columns, nil versus zero, missing/
extra/duplicate rows, wrong parent identity/type/level, OCR-style label typo,
empty inputs, ambiguous alignment ties, optional column assignment, file loading,
aggregation and CLI. Accounting tests include nested sums/net rows, nil/invalid,
tolerance boundaries, signed interval bounds, balance and missing subtotal.
Fault counts are derived independently from data, not hard-coded financial values.

Tests exposed two new-evaluator bugs, repaired here: role presence alone did not
check column assignment, and tuple dependency cells did not round-trip identically
through JSON. Neither fix changes parser behavior. Reports were regenerated after
these evaluator corrections; all existing parser assertions remain intact.

Limitations: one page; rules designed after seeing it; AI-drafted GT verified by
one human (with an independently reported second review); truncation hypothesis
rests on one page. File schema validation is intentionally small, not a general
hostile-input validator. Ambiguous repeated full paths need better GT identity.
Correlated/multiple faults, other documents/languages, scanned input, wrapped or
multi-page tables are not measured. An accounting pass can coexist with wrong
extraction or disappear as checks become not_evaluable. Read all denominators,
statuses, mismatch records and the failure analysis together.

Validation: full suite **275 passed in 8.73s**, from a 223-test baseline.
`python -m ruff check src scripts tests eval`: **All checks passed!**
All 19 protected-file baseline hashes match, including the unchanged UTF-8-BOM
GT CSV, raw PDF, examples, original parser modules and dependency manifests.


## P10b audit and measured geometry limits

P10 was applied in a different session/tool, then checked in an audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit, against
commit e40462b (283 tests). Existing successful fixes were preserved. The new
oracle independently generates digit/sign/nil mutations and directly computes
two arithmetic residuals (a four-addend subtotal and a gross/contra/net check),
without importing library fault generation or accounting-check logic.

Rows, right-edge columns and indentation share consecutive-gap single linkage
in rows._clusters. Defaults remain row0.35H, column0.30H, indent0.40H. Clustering
and cell assignment are distinct: after clustering establishes a median right
edge, _cells still accepts only tokens within0.30H of that edge. All20 x=.3 seeds
find two correct chronological columns, yet this assignment gate loses cells in
90 row-seed cases. Label contamination comes from those leftover numeric tokens;
no pure label-token spacing/order errors were observed. Indent splitting changes
81 row-seed indices but changes only two parents (seed5, rows14 and43).

At y=.2/.3H there are no cross-source-row merges in the measured20 seeds;
within-row consecutive gaps exceed0.35H and split words that moved independently.
The median original body pitch is1.338690H; row24 seed11 gap is0.350053H.
A 1.3H-pitch synthetic jitter test guards against merging adjacent row identities.

An optional in-memory candidate estimated median pitch from provisional groups
and used clamp(0.45*pitch, existing0.35H,0.65H), leaving a separation margin below
half-pitch. It restored43 rows at seed11 but immediately failed the existing
44-row failure-recording test. Per stop-at-first-problem/no-test-weakening rules,
the candidate was rejected and restored within minutes, well inside20 minutes.
No production pitch threshold was implemented; no candidate-wide robustness
claim is made. See p10_pitch_trial.json and p10_diagnose.py --pitch-trial.

Warnings: no_columns_detected for zero supported columns, one_column_detected
for one, no_body_rows for no reconstructed body, and empty_input from hierarchy
when there are no typed rows. Page JSON and parse CLI surface them. Default
unlisted all-negative lines stay line_item with possible_contra_or_loss.

Full P8/P10/current means/minima, ablations and fault counts are in
failure_analysis.md. P10b changes reporting/tests/warnings, not clustering defaults.
Schema issues for missing fields/raw columns return Table.issues; malformed row
identities still raise explicitly and are outside that schema-only fix.
