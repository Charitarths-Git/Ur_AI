# Page 4 ground truth — VERIFIED

Human verification confirmed on 2026-10-23 (Asia/Calcutta); `verified_by_human` is true.
The user checked all 43 rows against the page image, including labels, raw values,
nil cells, △0 and hierarchy columns, and reported an independent second review
with no discrepancies. No corrections were needed; the CSV bytes are unchanged.

- File: data/gt/page4.csv, UTF-8 with BOM (utf-8-sig), one row per printed table-body row, in reading order, from 資産の部 down to 資産合計. Page header items (訂正後, title, unit, period headings, footer) are NOT rows; they go in page4_meta.json.
- Columns: row_id, label, parent, parent_path, level, row_type, previous_year_value, current_year_value, prev_raw, curr_raw.
- label: exactly as printed (keep full-width parentheses （純額）, no normalization).
- parent_path: ancestors' labels joined by " > ", root first; empty for the root. parent: the immediate parent label. level = number of ancestors (so the root 資産の部 has level 0).
- Hierarchy convention (semantic, not just indentation):
  * 流動資産 and 固定資産 are children of 資産の部. 有形固定資産, 無形固定資産 and 投資その他の資産 are children of 固定資産.
  * Plain line items are children of their section header.
  * Where a gross item is followed by a 減価償却累計額 row and a （純額） row, those two rows are CHILDREN OF THE GROSS ITEM (e.g. parent of 減価償却累計額 is 建物及び構築物). The gross item itself is a child of the section.
  * A 合計 row is a child of the section it closes and has row_type subtotal; 資産合計 is a child of 資産の部 with row_type total.
- row_type values (exactly these): header (no numbers), line_item, contra (減価償却累計額 and 貸倒引当金), net (（純額） rows), subtotal, total.
- Values: integers in 千円 exactly as printed (do NOT multiply by 1000). △ means negative. A printed nil mark (－) is stored as an EMPTY value (null, not 0) and prev_raw/curr_raw keep the printed string. △0 is stored as 0 with raw "△0". prev_raw/curr_raw hold the string exactly as printed (including △, commas); empty for header rows. Use previous = 前連結会計年度 column, current = 当連結会計年度 column.
- If you believe a convention above is ambiguous or wrong for this page, say so in the report rather than silently deviating.


## Provenance

Transcribed visually from `data/derived/page4_200dpi.png` and overlapping
300 DPI crops rendered by `scripts/render_gt_crops.py`. No text extraction
was used for transcription. The later text-layer cross-check is read-only
and does not replace human adjudication. Nil values are empty CSV fields, never zero.
