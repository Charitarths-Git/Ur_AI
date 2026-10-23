# P14 implementation and evidence

## Frozen state and scope

Starting commit3e14d249ba755a9c12a4975f562c1224feb3464e was clean. Parser sources,
original PDFs, verified GT, examples and prior evaluation artifacts are identified
by SHA-256 in eval/versions/3e14d24/manifest.json; prior reports/examples are copied
there. Original parser remains available at that immutable Git revision. Source
PDFs and verified GT were not edited. Candidate parser33025ad was frozen before
held-out predictions. Later evaluator/log/documentation changes do not tune it.

## Header and reconstruction

rows._header_boundary considers dates only above the first supported value row,
in column-relative heading bands, and requires a unique date per detected column.
Fallbacks retain earlier behavior and add header_dates_missing/ambiguous or
header_unidentified. Footer dates and dates in body labels cannot erase prior rows.
Tests cover genuine headings, missing/ambiguous headings and a real-page footer date.
Numeric recovery uses at most twice the joining tolerance and stays inside the
nearest column midpoint. Nonnumeric/invalid fragments retain the strict gate.
No document coordinates, labels, values or row counts are in these heuristics.

Review flags: invalid_amount, incomplete_value_row, unassigned_numeric_token and
orphan_amount_row. Existing ambiguous_column_roles and insufficient_indentation
remain. Warnings propagate to exported JSON and CLI; layout-origin row IDs identify
visual row indices as printed by dump_rows.py (not necessarily exported tree IDs).
Raw strings, source PDF provenance and diagnostic row y-bounds remain available;
source_words retains original boxes in the in-memory layout. No confidence
probabilities are invented. Empty-body/column CLI output returns2; usable output
including warnings returns0. Warnings do not guarantee all semantic errors detected.

Limits: pooled columns do not segment multiple tables, early supported numeric
notes can defeat the first-body anchor, absent dates can lose leading headers,
and ambiguous heading layouts cannot be recovered reliably. Weak indentation
and high y noise remain difficult. The rejected historical pitch candidate was
not reinstated. The seed-11 y=.2H split regression remains intentionally present.

## JSON evaluator

See notes/evaluation_design.md for report schema1.1, independent tree traversal,
identity-based CSV consistency, separate JSON/GT alignment and CLI exit semantics.
Tests include empty tree, dropped node, false nesting with rewritten level,
duplicate/missing IDs, modified values, malformed children/JSON/schema and a
correct export. Source/page metadata field types and ISO dates are validated.
Fully correct-row metrics retain their historical definition; raw and schema
errors independently prevent a perfect validation result.

## Measurements and regressions

All geometry seeds, ablations and3817 faults rerun in eval/results/p14. The old
results remain unchanged under eval/results/robustness_report.* and the versioned
snapshot. comparison.md contains all before/after means/minima and regressions.
x=.3H cells .9360465→1.0 and parents .9639535→.9976744; y=.3H cells remain
.8889535 with minimum0. At y=.5H cells .3866279→.3843023, rowF1 .7974540→.7906201,
parents .8581395→.7534884. The change is not uniformly better. Lower accounting
pass rates sometimes accompany higher evaluable coverage; read both denominators.

Fault results are identical to baseline:3256/3673 digits,71/72 sign flips,
71/72 nil/blank faults. Flattened indentation retains38/43 parents and14/43 fully
correct rows. Accounting tolerance is unchanged. Original P8/P10 regressions and
pitch-threshold rejection remain in notes/failure_analysis.md and notes/p10_audit.md.

Five additional pages, two development and three held-out issuers, were scored
with original/candidate parsers and a fixed pdfplumber baseline. See benchmarks/
for provenance, annotations, initial-error corrections and review procedure;
eval/results/benchmark has final per-page/pooled metrics and actual timing samples.
Original/candidate held-out cells262/262, fully correct129/131; pdfplumber250/262
cells and hierarchy/types N/A. Candidate does not improve clean held-out scores.
No annotation is claimed human-verified or independently checked. Initial
annotation mistakes were corrected by the same agent after image reinspection;
initial results remain in benchmark_initial_annotations. Semantic disagreements
include standalone net amounts, treasury-stock type and final balance total type.

## Maintenance

export_chat defaults to outputs/chat_export and refuses existing outputs without
--replace. Input is validated before writes; both staged products are prepared,
then originals are backed up before explicit replacement. Backup tests ensure
byte-identical recoverability. Original consolidated logs remain unchanged;
a36-message visible conversation supplement states each source cutoff. No raw
reasoning/platform instructions or tool payloads are exported. An active session
is not claimed complete; no new Claude web log was available.

GitHub Actions is configured for Windows/Python3.14, pinned requirements, pytest
and Ruff. It downloads dependencies only, never benchmark PDFs. CI execution is
reported separately from configuration. New benchmark PDFs are not redistributed;
official URL/hash retrieval and review rendering are explicit commands.

## Final verification

The final verification record is in notes/p14_verification.json. It records actual
test counts, lint, supplied output hashes and original protected-file checks.
README and REPORT commands use versioned robustness output and explicit benchmark
downloads. Human annotation review remains future work; OCR/VLM, model training
and GPU serving were deliberately outside scope. The submission email is a draft.
