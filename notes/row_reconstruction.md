# P4 row reconstruction and indent clustering

## Boundary and public API

`parser.layout_types` defines frozen Word, Rule, RawPage, LayoutConfig,
LayoutThresholds, Column, Cell, Row and PageLayout dataclasses. Collections are
immutable tuples; RawPage accepts and freezes word/rule iterables.
`parser.pdf_backend.PageBackend` is a small protocol with
`read_page(path, page_number=1, config=LayoutConfig()) -> RawPage`.
`PyMuPDFBackend` implements it; `read_pdf_page` is the convenience function.
PDF page numbers are one-based, independent of the filing's printed page number.
Only pdf_backend.py imports pymupdf inside the package. Existing P1/P2 standalone
diagnostic/rendering scripts retain their original extraction imports.
No OCR or VLM implementation has been added.

`parser.rows.reconstruct_page(raw_page, config=LayoutConfig()) -> PageLayout`
is pure. It reads no files and imports no PDF library or GT. P3 normalize.py is
unchanged. Rows expose zero-based visual indices, zone, bbox, unnormalized label,
raw label_x0, visual indent_step, cells, rule_above and original source words.
Cells retain raw strings and AmountResult. Columns expose a zero-based index,
right-edge centre, collected heading text and parsed period_end. No parents,
levels, semantic row types, accounting rules, exporters or evaluation modules
are present.

## Algorithm and decisions

1. Ignore whitespace-only tokens (using label_key solely as an emptiness check)
   and nonpositive-height boxes. Use the median positive word bbox height H,
   not font size. With no usable words use page height times the configured
   fallback fraction. Raw text is never normalized for labels or cells.
2. Sort by vertical centre, with deterministic x/text tie-breakers. Group against
   the running median centre within the row tolerance, then sort each row by x.
   Running-median grouping avoids unrestricted adjacent-gap chaining.
3. Merge an immediately preceding single sign token with a parseable unsigned
   digit token only within sign_gap (small overlap up to column_tolerance is
   allowed). Keep both original words as provenance. Fused tokens remain intact.
4. Cluster right edges of tokens accepted by parse_amount as ok or nil. Require
   distinct supporting rows, not repeated tokens on one row. The cluster median
   is the value-column anchor. Thus isolated title/footer digits and label digits
   cannot establish a column. There is no assumed number of columns.
5. Assign tokens by right-edge proximity, including invalid tokens in an
   established column. Multiple fragments assigned to a cell are retained and
   separated by a space, so ambiguity is visible through an invalid parse rather
   than silently discarded. Only the explicitly merged sign/digits omit a space.
6. The last visual row containing a complete parse_period_end date ends the
   header. Without such a row, the first supported valid/nil value row begins
   the body; preceding label-only rows remain header. Body ends at the last
   aligned cell, including invalid cells. Everything thereafter is footer.
   Without supported cells, all nonempty rows are header. Header/footer rows
   retain their complete text as labels and expose no value cells.
7. Body labels are the remaining original words in x order. Insert a space only
   if the gap exceeds label_space_gap, preserving existing token whitespace.
   No NFKC, stripping or accounting-word logic is applied to output labels.
8. Header ownership uses column bands ending at the right-edge centres. Interior
   bands start at the preceding centre; extrapolate the first gap for the first
   band. A lone column uses its observed token starts plus heading padding.
   Collect header tokens whose horizontal centres fall in the band, preserve
   line breaks and call parse_period_end separately per column. There is no
   previous/current mapping. Consequently units may be collected with a column
   heading; on this page they appear in column 1. Nothing is stripped semantically.
9. Cluster body label_x0 against a running median, using indent_tolerance. Number
   visual steps left to right and retain the raw positions. This is not hierarchy.
10. Keep only thin horizontal rectangles/segments: height <= rule_max_height and
    width >= rule_min_width. For line segments height includes stroke width.
    In pure reconstruction recheck these limits, then mark rule_above if the
    primitive lies in the gap after the preceding visual row and before this
    row, allowing vertical slack, and overlaps an observed body-value ink span
    horizontally (with column_tolerance slack). Wide shaded backgrounds fail
    the height test. Rule evidence is not an accounting interpretation.

## All thresholds

Distances below multiply H; there are no hard-coded point coordinates. Support
is a row-count requirement, not a geometric threshold. Every default is in
LayoutConfig; PageLayout.thresholds records the actual distances used.

| Config field | Default | Purpose |
|---|---:|---|
| row_tolerance | 0.35 H | baseline jitter within a visual row |
| column_tolerance | 0.30 H | right-edge grouping and assignment; horizontal overlap slack |
| column_min_support | 3 distinct rows | reject isolated parseable title/footer/label tokens |
| label_space_gap | 0.35 H | preserve visibly separated label words |
| sign_gap | 0.60 H | merge adjacent split signs with digits |
| indent_tolerance | 0.40 H | group jittered label left edges |
| rule_max_height | 0.15 H | reject thick fills/shading |
| rule_min_width | 2.00 H | reject short/nonhorizontal shapes |
| rule_vertical_tolerance | 0.10 H | slack between rules and adjacent row bboxes |
| single_column_heading_pad | 2.00 H | left extension if only one column exists |
| fallback_height_fraction | 0.01 of page height | missing usable word heights only |

## Observed real-page results

Source: backend extraction from the original PDF (PDF page 1, printed page 4).
No GT was used to choose thresholds or reconstruct the page.

| Actual quantity | Value (PDF points unless stated) |
|---|---:|
| median_word_height | 8.963989 |
| row_tolerance | 3.137396 |
| column_tolerance | 2.689197 |
| label_space_gap | 3.137396 |
| sign_gap | 5.378394 |
| indent_tolerance | 3.585596 |
| rule_max_height | 1.344598 |
| rule_min_width | 17.927979 |
| rule_vertical_tolerance | 0.896399 |
| single_column_heading_pad | 17.927979 |
| column_min_support | 3.000000 |

Column centres: 397.513123, 522.553162.
Indent centres: 62.279999, 75.239998, 88.199997, 101.279999, 114.239998.
Zones: header=6, body=43, footer=1.
Backend: 132 words; 58 retained thin rule primitives.

Column 0 heading (period_end=(2025, 3, 31)):

```text
前連結会計年度
(2025年３月31日)
```

Column 1 heading (period_end=(2026, 3, 31)):

```text
（単位：千円）
当連結会計年度
(2026年３月31日)
```

## Read-only GT comparison and informational cross-tabs

Integration reads the verified CSV and metadata with utf-8-sig. It checks body
row count, labels via label_key, all raw value strings and integer/null values,
empty cells on section headers, two columns and their dates against metadata.
All 43 body rows and 74 printed value cells match; section header rows have no
cells. GT labels, financial values and row counts are never algorithm inputs.
Exact label matching is reported below, not asserted. Neither cross-tab is an
assertion or a rule for a later phase.

Exact label matches: 43/43; labels with internal spaces: 0.

| GT row_type | rule_above=False | rule_above=True |
|---|---:|---:|
| contra | 5 | 0 |
| header | 2 | 4 |
| line_item | 16 | 6 |
| net | 0 | 4 |
| subtotal | 0 | 5 |
| total | 0 | 1 |

| indent_step | GT level 0 | GT level 1 | GT level 2 | GT level 3 | GT level 4 |
|---|---:|---:|---:|---:|---:|
| 0 | 1 | 0 | 0 | 0 | 0 |
| 1 | 0 | 3 | 0 | 0 | 0 |
| 2 | 0 | 0 | 15 | 0 | 0 |
| 3 | 0 | 0 | 0 | 16 | 0 |
| 4 | 0 | 0 | 0 | 0 | 8 |

The footer also has rule_above=True: the final body underline lies between it
and the preceding row. This illustrates why the flag is evidence, not a role.

## Validation

Targeted tests/test_rows.py: 25 passed in 6.19s before final formatting.
Twelve invariance cases cover both synthetic and real inputs: shuffled words
and rules, translation (-240,+375), scales 0.45 and 2.75, combined scale 1.7
with translation (+220,-400) and shuffling, and per-word x/y jitter uniformly
bounded by 0.015 H (about 0.1345 pt on this page), with shuffling. All pass.
Signatures compare labels, raw/parsed cells, zones, indent steps, rule flags and
column headings/dates. Scaling additionally checks threshold scaling, and
translation checks indent-centre translation. Mixed font heights and baseline
jitter are covered separately. Jitter is intentionally bounded away from the
heuristics' decision boundaries, not a claim of invariance for arbitrary noise.
Both dump_rows.py and inspect_pdf.py pass subprocess tests with PYTHONIOENCODING
and PYTHONUTF8 removed and Python UTF-8 mode explicitly disabled (-X utf8=0).
A shared stdlib console helper configures stdout/stderr as UTF-8 at CLI startup;
all preexisting scripts use it too. Existing P1/P2 extraction behavior is retained.
Final full-suite and ruff results are recorded in workstamp.md and appended below.

## Known limitations

- Wrapped labels remain separate visual rows; there is no continuation merging.
- Multi-line headings are collected by bands, but a date split across visual
  rows cannot anchor the header boundary; the no-date fallback may omit leading
  label-only body rows. Titles/units inside a column band remain in its heading.
- Tables spanning pages are not joined; each page is processed independently.
- Label-only last rows become footer; label-only first rows become header when
  no complete date row supplies a better boundary. Aligned numeric footer text
  can extend the body; dates within body text can wrongly extend the header.
- Sub-column headings/grouped headers are not interpreted or split semantically.
- Rotated PDFs are explicitly rejected by the default backend. Scanned pages
  need a future OCR/VLM backend; this adapter does not recognize image text.
- Multiple tables on one page are not segmented. Columns may be pooled and the
  last date row may hide an earlier table inside the header zone.
- Short tables below column_min_support, or columns containing only invalid
  tokens, cannot establish columns unless configured otherwise. Repeated label
  digits aligned across enough rows can resemble a column. Proportional or
  left-aligned numeric layouts are unsupported by this right-edge heuristic.
- Bounded jitter works within the tested margins. Noise near row/column/space/
  indent boundaries, dramatic mixed font heights, overlapping text, or bridges
  between clusters can change the result. User config can adjust thresholds.
- Rules must fit between consecutive word bboxes; crossing/touching tall text
  beyond the configured slack may be missed. Dashed/curved borders and color
  semantics are not interpreted. Thin decorative bars may still be evidence.
