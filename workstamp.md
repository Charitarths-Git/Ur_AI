# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P2 |
| State | IN PROGRESS |
| Updated | 2026-10-22T18:00:38Z |

## Current prompt (verbatim)

## P2: Ground truth (draft for human verification)
Copy this whole P2 section verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P2 IN PROGRESS, mark steps [~]/[x] as you go, and make small wip(P2) commits.

Goal: create a hand-verifiable ground-truth table for page 4, created from the RENDERED PAGE IMAGE, independent of any parser. A human (me) will verify it against the page afterwards. Do not write any parsing, normalization or evaluation code for the package.

### Rules for independence (important)
- Transcribe ONLY from the image data/derived/page4_200dpi.png. If your tooling cannot view images, STOP and tell me; do not fall back to the text layer.
- If digits are hard to read at 200 DPI, render zoomed crops of the PDF with PyMuPDF (e.g. 300 DPI, horizontal strips of about 12 rows with overlap) into data/derived/crops/ and read those. Rendering crops is allowed; reading text from the PDF is NOT allowed during transcription.
- During transcription do NOT open or use: the PDF text layer, get_text, pdfplumber, notes/words_*.json, notes/inspection.md. Do not copy numbers from earlier chat output or from any file other than the images.
- If any character or digit is unclear, do not guess: write the best reading and list it under "uncertain cells" in your report.

### Step 0 (before transcription): verify one P1 claim
notes/inspection.md Q6 reports 39 rows with numbers and 11 without. I suspect 2 of the "numeric" rows are the date heading and the "- 4 -" footer, which contain digits but are not data rows. Check this from the P1 notes only (not for GT purposes), and if Q6 is wrong or misleading, correct that paragraph of notes/inspection.md with evidence and commit it as a separate "fix(P1): ..." commit. This does not count as using the text layer for GT.

### Step 1: define the ground-truth conventions
Write data/gt/README.md documenting these conventions exactly:
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

### Step 2: transcribe
Create data/gt/page4.csv and data/gt/page4_meta.json (page_number, correction_marker "訂正後", title, unit "千円", period headings as printed, period end dates as printed, "verified_by_human": false). Number of rows: report what you count; do not pad.

### Step 3: verification aids (not part of the package)
a) Write notes/gt_verification.md: a checklist table with one line per GT row (row_id, label, previous raw, current raw, a "[ ] verified" box) so I can tick rows against the page.
b) Write a throwaway script scripts/gt_selfcheck.py that (1) validates the CSV schema, enums, level == number of path elements, and that nil cells are empty; and (2) prints, for each subtotal/net/total row, the components' sum vs the printed value and the difference, as INFORMATION ONLY (no pass/fail, no tolerance logic; that is P7).
c) ONLY AFTER the CSV is finished and committed: write scripts/gt_crosscheck.py that compares GT numbers against the numeric tokens in the text layer and prints disagreements. It must never modify the GT. Report disagreements; do not fix them by yourself, because I adjudicate against the page.

### Constraints
- Do not use the text layer for GT values; do not invent data; do not touch the original PDF; do not add anything under src/.
- Add one pytest test that only checks schema (columns present, allowed row_type values, level consistent with parent_path). Assert NO financial values and no row counts.
- Run the full test suite. Update README (data/gt description, how to run the two scripts).
- Final commit "P2: draft ground truth (pending human verification)"; workstamp.md set to DONE with "Next action: human verification of GT, then P3". Mark in workstamp.md that the GT is a DRAFT until I confirm.

### Final message must show
Orientation results (repo state, tests, session row added); row count and row-type counts; the list of uncertain cells; the self-check output; the cross-check disagreements (if any); convention questions; files created; test output; commit hashes.

## Plan for this prompt

1. [x] Orient: read brief/handoff, clean git status, log, baseline tests; add session.
2. [x] Verify P1 Q6 from notes only; correct misleading count in separate fix(P1) commit.
3. [x] Document exact ground-truth conventions.
4. [x] View rendered page/crops, transcribe CSV and metadata; commit completed CSV before text cross-check.
5. [x] Add human checklist, informational self-check, one schema-only pytest test.
6. [~] After CSV commit, implement read-only text-layer cross-check and report disagreements.
7. [ ] Update README, run full suite, record output and finalize draft handoff/commit.

## Files created or modified

- notes/gt_verification.md — one checklist row per GT row and metadata/hierarchy checks.
- scripts/gt_selfcheck.py — schema/nil validation and informational arithmetic.
- tests/test_gt_schema.py — one schema-only test; no financial or row-count assertions.

- data/gt/README.md — prescribed conventions and provenance.
- data/gt/page4.csv — 43 image-transcribed DRAFT body rows, UTF-8 BOM.
- data/gt/page4_meta.json — image-transcribed page metadata, human verification false.
- scripts/render_gt_crops.py and data/derived/crops/ — image-only visual review aids.

- notes/inspection.md — notes-only Q6 and summary correction, with coordinate evidence.

- workstamp.md — P2 prompt, plan, orientation evidence and Session 5.

## Last action and result

Verification aids completed: per-row human checklist, schema-only pytest and
informational arithmetic script. Self-check schema OK; all 10 net/subtotal/total
relations printed for both years, differences range from -3 to +1 千円. Null
components explicitly listed; no financial pass/fail or tolerance applied.
CSV freeze commit: 7ca2ef81fc11039598a95aae611b8ec9433df90c.

Image transcription finished: 43 rows, header=6, line_item=22, contra=5, net=4,
subtotal=5, total=1. CSV written as UTF-8 with BOM; metadata is DRAFT/false.
Read full page plus heading and four overlapping body crops at 300 DPI. No
uncertain numeric/label cells identified. No text-layer access during transcription.
Conventions/crop renderer commit: ff2d8e1. CSV must now be committed before cross-check.

Conventions copied exactly into data/gt/README.md. Viewed the entire 200 DPI
page; preparing overlapping 300 DPI image-only crops for careful digit review.
Latest commit: 9a0e517 (separate P1 correction).

P1 Q6 audit complete: 39/11 was page-wide, including date/footer; corrected to
37 numeric body rows and six body headers. Orientation WIP: 4d98884.

Orientation: clean working tree at a46ee03; git log -5 confirms P1 final 0597652
and handoff update 0c66de8. Full suite: 11 passed in 2.22s (Python 3.14.0,
pytest 9.1.1, venv interpreter, PYTHONIOENCODING=utf-8).
P1 is DONE as recorded. Its stale “Final commit pending” line was superseded
by verified commit history. No implementation inconsistencies found.

## Decisions and assumptions

- Repository is the only continuity source. Actual model identity supplied to this agent: GPT-6 (Codex).
- GT is a DRAFT until the human explicitly confirms it; verified_by_human remains false.
- Step 0 may read P1 notes for count correction only; transcription uses images exclusively.
- No package changes under src/; original PDF must remain unchanged.

## Known issues / open questions

- No unresolved orientation issues. P1 Q6 corrected: 37 numeric body + 6 body headers; 7 page-level rows.

## Next action

Create and run read-only text-layer cross-check; preserve frozen GT unchanged.

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
