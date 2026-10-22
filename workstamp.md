# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P2 |
| State | DONE |
| Updated | 2026-10-22T18:09:36Z |

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
6. [x] After CSV commit, implement read-only text-layer cross-check and report disagreements.
7. [x] Update README, run full suite, record output and finalize draft handoff/commit.

## Files created or modified

- data/gt/README.md — exact supplied conventions; DRAFT/provenance notice.
- data/gt/page4.csv — 43 image-derived body rows, UTF-8 BOM, null nil cells.
- data/gt/page4_meta.json — image-derived page/period metadata, verified_by_human=false.
- data/derived/crops/ — heading + four overlapping 300 DPI body crops.
- scripts/render_gt_crops.py — image rendering only, reproducible visual aids.
- scripts/gt_selfcheck.py — schema checks and informational sums/differences.
- scripts/gt_crosscheck.py — read-only text-layer comparison, written after CSV commit.
- tests/test_gt_schema.py — one schema-only test; no financial or row-count assertions.
- notes/gt_verification.md — checklist for all GT rows plus metadata/hierarchy.
- notes/p2_report.md — complete captured self-check, cross-check and test outputs.
- notes/inspection.md — separate P1 Q6 count/summary correction.
- README.md — DRAFT status, data/gt description and script commands.
- workstamp.md — P2 prompt/plan, session, evidence and handoff.

## Last action and result

Final checks: full suite 12 passed in 1.82s; new-file ruff checks pass;
git diff --check passes. Verbatim P2 section matches the supplied file.
Cross-check compared 74 cells (37 per column), zero disagreements; working CSV
SHA-256 unchanged: c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835.
GT content is unchanged from image-only freeze 7ca2ef8 (Git stores LF while the
working CSV writer uses CRLF; a first raw-blob equality check was corrected to
account for this). Original PDF and src/ unchanged relative to baseline a46ee03.

Orientation: clean tree at a46ee03; P1 DONE at 0597652; baseline 11 passed in
2.22s. Stale P1 “Final commit pending” note superseded by verified Git history.

Commits so far: 4d98884 orientation; 9a0e517 separate fix(P1); ff2d8e1 conventions;
7ca2ef8 independent image-derived CSV; 43d8298 verification aids;
8695260 read-only cross-check and documentation. Final P2 commit succeeded:
0be2cf6cb6d9fba788d1395adf2b0ceebcd5b14f — P2: draft ground truth (pending human verification).
This metadata-only follow-up records the final hash and DONE status, as in P1.

## Decisions and assumptions

- Actual model identity supplied to this agent: GPT-6 (Codex); Session 5 added.
- GT is a DRAFT until human confirmation; verified_by_human remains false.
- Q6 audit used P1 notes only, before transcription: 37 numeric body + 6 headers;
  date row/footer and five page headers are excluded from the 43 body rows.
- Transcription used only the full 200 DPI image and five 300 DPI crops. No PDF
  text layer, word dumps or P1 notes accessed during transcription.
- CSV was completed and committed in 7ca2ef8 BEFORE cross-check code was written.
- Row counts: header=6, line_item=22, contra=5, net=4, subtotal=5, total=1.
- Nil cells stay null; sums of present components explicitly list omitted nulls.
  Arithmetic differences (-3 to +1 千円) are information only, with no tolerance
  or financial pass/fail; printed values were not changed to force agreement.
- No new dependencies, package parsing/normalization/evaluation code or src/ changes.

## Known issues / open questions

- Uncertain cells: none identified after enlarged visual review.
- Convention questions/deviations: none.
- Human verification is outstanding by design; do not start P3 before confirmation.

## Next action

human verification of GT, then P3

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | DRAFT image-derived GT, 43 rows, pending human verification; 12 tests pass | 0be2cf6 |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
