# P5–P6: classification, hierarchy, metadata and exports

## Validation boundary

**Only the supplied printed page 4 has been validated against a real document.**
Liability/equity totals, 自己株式, correction-before markers and other units are
untested real-document heuristics. Some have synthetic unit tests; that does not
validate their accounting meaning on another statement. No general accuracy
claim or P7 evaluation module is made here.

Orientation: clean tree at 9012bae; baseline 166 passed in 6.73s. Session 5
continues. Verified GT and raw PDF are read-only. P3 normalization and all P4
production modules were unchanged in P5–P6; P10 later changed clustering, and
P10b audited it and added explicit empty/one-column warnings.

## Small corrections

- Q5 in notes/inspection.md now counts five visual body indent steps including
  the root, using the P4 centres as evidence. Steps are not semantic levels.
- P4 deliberately keeps original heading evidence. Metadata removes whole unit
  lines from column headings, using a RuleSet regex on label_key. The exported
  right-column heading no longer contains the unit line. A regression test
  preserves the raw input heading and checks the cleaned output.

## RuleSet

RuleSet is frozen, copies pattern sequences to tuples, and freezes a copied unit
map with MappingProxyType. The logic contains no Japanese accounting strings.
All exact/prefix/suffix and metadata-regex matching uses label_key; printed row
labels, title lines and non-unit heading characters are preserved for output.
Regex patterns target normalized, whitespace-free comparison keys and must use
named groups `unit` and `page` where appropriate. Correction pairs explicitly
map a printed marker to its metadata value without surrounding parentheses.

| Field | Default JA_FINANCIAL_STATEMENT pattern/value | Real-document validation |
|---|---|---|
| total_labels | 資産合計 | Validated on page 4 only |
| total_labels | 負債純資産合計; 負債及び純資産合計; 負債・純資産合計 | Untested heuristic |
| total_suffixes | Empty; custom RuleSets may supply suffixes | No default heuristic |
| subtotal_suffixes | 合計 | Validated on page 4 only |
| net_suffixes | （純額）; (純額), identical after label_key | Validated on page 4 only |
| contra_labels, prefix/exact | 減価償却累計額; 貸倒引当金 | Validated on page 4 only |
| contra_labels, prefix/exact | 自己株式 | Untested heuristic |
| all_negative_cells evidence | No classification rule; unlisted negatives warn possible_contra_or_loss and remain line_item | Synthetic 営業損失 regression; page4 contras all use explicit label prefixes |
| unit_pattern | `\(単位:(?P<unit>[^()]+)\)` on comparison keys | 千円 line validated on page 4 only |
| unit_multipliers | 千円 → 1000 | Validated as metadata on page 4; never applied to cell values |
| unit_multipliers | 百万円 → 1000000; 円 → 1 | Untested real-document heuristics; synthetic parsing tests only |
| correction_markers | （訂正後） → 訂正後 | Validated on page 4 only |
| correction_markers | （訂正前） → 訂正前 | Untested heuristic |
| page_number_pattern | `-(?P<page>[0-9]+)-` on comparison keys | Printed `- 4 -` validated; other pages unvalidated |

## Classification and independent evidence

Order: no cells → header; total exact/suffix; net suffix; subtotal suffix;
contra prefix; then structural line_item fallback. All valid numeric cells printed
negative is evidence only: without a listed contra prefix, emit
possible_contra_or_loss on the row and page. It cannot distinguish a contra from
a loss such as 営業損失. No-cells takes precedence even if a
label contains a total keyword. Nil and invalid cells are not numeric for sign
evidence; with no valid numeric cells, all-negative is false. Printed △0 is a
valid numeric negative representation and contributes true negative evidence.

Every TypedRow retains type_source (`label_rule` or `structural`), rule_above,
all_negative_cells, no_cells, has_negative_cells and typed ParseWarning objects.
Label-based subtotal/net/total without a rule emits missing_rule_above; a contra
without any negative numeric cell emits contra_without_negative. Mixed signs do
not undo an explicit contra label. Conflicts warn rather than override the type.
Headers with rules do not warn. Unlabeled value rows are kept and warned.

Observed evidence counts (independent columns, not semantic inference rules):

| Row type | Count | Rule false | Rule true | All-negative false | All-negative true | No cells |
|---|---:|---:|---:|---:|---:|---:|
| header | 6 | 2 | 4 | 6 | 0 | 6 |
| line_item | 22 | 16 | 6 | 22 | 0 | 0 |
| contra | 5 | 5 | 0 | 0 | 5 | 0 |
| net | 4 | 0 | 4 | 4 | 0 | 0 |
| subtotal | 5 | 0 | 5 | 5 | 0 | 0 |
| total | 1 | 0 | 1 | 1 | 0 | 0 |

Real-page warnings: **empty**. Four ruled headers are intentionally accepted.

## Hierarchy and paths

With at least two distinct nonmissing body indent steps, maintain a stack.
Pop rows whose step is greater than or equal to the current step; the remaining
top is the nearest earlier strictly smaller step and becomes the parent. Row IDs
are integers starting at 1 among body rows only. Paths use printed ancestor
labels joined by ` > `; levels count ancestors, never copy indent_step. Duplicate
labels are disambiguated by row ID and context. Build immutable TreeRow objects
with explicit children and an ordered root forest. A first row that is not the
least indented and upward jumps exceeding one step generate typed warnings.
A missing-step row attaches to active context with a warning, without becoming
a new indentation anchor. No GT data is accessed by this algorithm.

With fewer than two distinct steps, hierarchy_source is rules_fallback and a
warning explicitly states that header nesting is unknown. The first body row
is the root. Later headers and totals attach to root; line items/subtotals attach
to the most recent header; contra/net rows attach to the nearest preceding line
item, with header/root only as a safety fallback if no such item exists. This is
deliberately partial. Empty input returns an empty forest with empty_input,
not the misleading insufficient_indentation warning. Zero supported value columns
emit no_columns_detected; one emits one_column_detected. No body emits
no_body_rows. These reach page JSON and the CLI summary.

On page 4, indentation produces the GT convention directly: each subtotal is
under its section, each contra/net pair under its gross item, and the final total
under the root. No special page-specific hierarchy overrides were added.

## Flat-indentation ablation: diagnostic only

Moved every body row's label tokens to the same x0, retaining their relative
spacing, all numeric ink, header/footer text and rules. Reconstructed and ran the
same pipeline. It does not crash; it reports rules_fallback and the typed
insufficient_indentation warning. All row types and values still equal GT.

**38/43 parent IDs agree with GT** in this controlled example. This is not an
accuracy claim. No parent-agreement score is asserted in the ablation test.

| Row ID | Label | Fallback parent | Expected parent | Reason |
|---|---|---|---|---|
| 12 | 貸倒引当金 | その他 (11) | 流動資産 (2) | Partial rule attaches every contra to the nearest line item |
| 15 | 有形固定資産 | 資産の部 (1) | 固定資産 (14) | Header nesting is unknown |
| 31 | 無形固定資産 | 資産の部 (1) | 固定資産 (14) | Header nesting is unknown |
| 35 | 投資その他の資産 | 資産の部 (1) | 固定資産 (14) | Header nesting is unknown |
| 42 | 固定資産合計 | 投資その他の資産 (35) | 固定資産 (14) | Latest header need not be the section a subtotal closes |

The fallback is left partial as requested; no fixes were derived from GT labels.

## Metadata and column roles

Only header/footer zones supply metadata. RuleSet matches identify correction,
unit and printed-page lines; complete dates and known column-heading text are
excluded from title candidates. Remaining printed header lines form title_lines;
JSON title joins them with newline. This page has both its section heading and
the balance-sheet subtitle. Missing fields stay None. Conflicting unit/correction
markers warn and retain the first observed value. An unknown unit can have a
unit string with a None multiplier; there is no guessed conversion.

Exactly two distinct known period dates map chronologically to previous_year
and current_year, even if the columns are reversed physically. Every other
case maps left-to-right to value_1..value_N with ambiguous_column_roles warning.
Column headings are cleaned of whole unit lines. Unit and multiplier are
metadata only; every amount remains in printed units.

Observed: correction 訂正後; unit 千円; multiplier 1000; printed page 4;
source PDF page 1. Column periods 2025-03-31 and 2026-03-31. Clean headings are
前連結会計年度 plus its date, and 当連結会計年度 plus its date.

## API, schemas and determinism

- classify_row / classify_rows: pure typing and evidence.
- build_hierarchy: pure typed-row ancestry, flat reading order and root forest.
- extract_metadata: pure metadata, cleaned columns/roles and warnings.
- parse_layout(layout, source_name, page_number=1, backend="pymupdf", rules=...):
  pure assembly into frozen ParsedPage. Source basename is retained, not a path.
- parse_page(path, page_number=1, layout_config=LayoutConfig(), rules=...):
  backend → P4 reconstruction → pure assembly. This is the PDF I/O boundary;
  actual PDF access remains in the P4 backend.
- csv_bytes / json_document / json_bytes: pure deterministic serializers.
- write_exports: explicit file I/O boundary; writes only requested output files.

The flat CSV is UTF-8 with BOM and LF, with these columns in this exact order:

```text
label,parent,level,row_type,previous_year_value,current_year_value,row_id,parent_row_id,parent_path,prev_raw,curr_raw
```

Without previous/current roles, value_1..value_N replace the two value fields,
and raw_1..raw_N replace prev_raw/curr_raw. Null values and missing/header cells
are empty CSV fields; raw strings retain signs, nil marks and commas. Invalid
cells also have empty values, with their raw preserved and JSON status invalid.

JSON is UTF-8 without BOM, ensure_ascii=False, indent=2, LF and final newline.
Top-level keys, in stable order: schema_version (1.0), source, page, columns,
hierarchy_source, warnings, rows. Source contains file basename, one-based PDF
page and backend. Page contains title, correction_marker, unit, unit_multiplier
and printed_page_number. Each column has index, role, cleaned heading, and ISO
period_end or null. Each node has row_id, printed label, row_type, level,
values keyed by role (raw/value/status), and ordered children. Missing cells
have raw empty, value null, status empty. No timestamps, coordinates, absolute
paths or environment-dependent floats enter either format. Typed evidence and
type_source remain available on ParsedPage rows via .typed; the prescribed file
schemas do not add these fields. Typed warnings export as code/message/row_id.

Committed examples contain the fresh real-page outputs. .gitattributes enforces
LF for these examples so fresh serializers match checked-out bytes on every OS.
outputs/ remains ignored. The CLI configures UTF-8 streams at startup and writes
<stem>_p<N>.csv/.json; its summary includes row counts, hierarchy source and warnings.

## Tests and observed field comparison

Every one of the 43 rows agrees with GT on each field: exact label, parent label,
parent_row_id, parent_path, level, row_type, previous_year_value,
current_year_value, prev_raw and curr_raw. Metadata unit, correction, printed page
and both column periods match GT. hierarchy_source is indentation; warnings empty.

Six real-page transformations (P4 helpers) produce byte-identical CSV and JSON:
shuffle, translate, scales 0.45 and 2.75, combined scale/translate/shuffle, bounded
jitter. Synthetic tests cover ordering, conflicts, gaps, forests, flat fallback,
unlabeled rows, empty input, replaceable rules, column-role ambiguity, units and
absent metadata. Export tests compare CSV/BOM/order, tree flattening, nulls,
invalid statuses, reversed dates, determinism, CLI and committed-example bytes.

An initial sandboxed targeted run passed 55 tests but pytest could not create
its temporary directory for the CLI fixture. Rerunning unchanged tests outside
the sandbox passed all 56 tests in 3.41s. One further date-only-header regression
was then added. Final full-suite and ruff results are recorded below and in workstamp.md.

## Known limitations

- Without indentation, header nesting and many contra/subtotal parents are unknown;
  fallback is intentionally partial and warned, including the documented ablation errors.
- Subtotals without keywords may be ordinary line items. Rule conflicts warn; they
  cannot discover correct semantics. A label-based contra may have mixed signs.
- Tables spanning pages are not joined; multiple tables on one page are not segmented.
- Label-less rows remain empty labels and warn; their parent context may be uncertain.
- Non-Japanese statements require a replacement RuleSet and fresh validation. Even
  Japanese liability/equity, other units and unobserved patterns are real-document heuristics.
- Scanned pages need a future backend. P4's rotated-page rejection, wrapped-label,
  boundary-zone, short-table and noise limitations continue to apply.
- Titles are remaining header text, so banners or incomplete column headings may
  be included. Multi-line units/markers and sub-column roles are not interpreted.
- An indentation forest can have multiple roots. Partial fallback may attach a
  later contra/net to an older item across sections; tree traversal can then differ
  from flat reading order. Row IDs retain reading order; no corrective guessing is done.

## Final validation

```text
python -m pytest
collected 223 items
test_export.py: 13 passed
test_hierarchy.py: 30 passed
test_metadata.py: 14 passed
Existing P0–P4 tests: 166 passed
223 passed in 7.88s

python -m ruff check src/parser scripts tests/test_hierarchy.py tests/test_metadata.py tests/test_export.py
All checks passed!
```

All GT/raw files have identical SHA-256 before and after work/tests. The original
PDF, verified CSV bytes/BOM, P3/P4 production code and dependency manifests are
unchanged. The verbatim user request is preserved. Generated examples are tested
against fresh in-memory serialization and a fresh CLI generation. No P7/P8 work
has started. The configured Git upstream is missing; no remote operation occurred.
