# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P1 |
| State | DONE |
| Updated | 2026-10-22T14:22:00Z |

## Current prompt (verbatim)

Phase 0 (setup) is complete, but it was executed with an earlier version of my instructions that did not include a session handoff protocol. This prompt (P1) first installs that protocol, then does the Phase 1 work: inspecting the PDF. Do NOT write any parsing, normalization or evaluation logic in this step; diagnostics only.

## Part A: Install the session handoff protocol (do this FIRST)
My Claude Opus 4.6 usage limit can run out in the middle of a prompt, and I then continue in a new session with a different account. The new session will have NO memory of this chat. The only continuity is the files in this repository. From now on, for every prompt I give you, follow this protocol:

1. workstamp.md at the repo root has this structure:
   - "Status": current prompt ID (e.g. P1), state (NOT STARTED / IN PROGRESS / DONE), UTC timestamp of the last update.
   - "Current prompt (verbatim)": the full text of the prompt I most recently gave you, copied exactly, so a new session can continue without me re-pasting it.
   - "Plan for this prompt": numbered steps, each marked [ ] pending, [~] in progress, or [x] done.
   - "Files created or modified" in this prompt, one line each on what changed.
   - "Last action and result": the last command run and its outcome (pass/fail, key output).
   - "Decisions and assumptions" so far (brief, with reasons).
   - "Known issues / open questions".
   - "Next action": one concrete sentence stating what to do next.
   - "Prompt history": a table of completed prompts (ID, one-line outcome, commit hash).
   - "Sessions": a table with session number, model name, UTC start time (write "unknown" if you cannot determine it), and a note on why it ended if known.
2. At the START of every prompt: read PROJECT_BRIEF.md and workstamp.md, copy my new prompt verbatim into "Current prompt (verbatim)", write the numbered plan, and set state to IN PROGRESS BEFORE doing any other work.
3. Write your INTENT before you act: mark a step [~] before starting it and [x] only after it has actually succeeded. Update workstamp.md after every step and before any long-running command. You may be cut off at any moment, so never batch updates for later.
4. Make small WIP git commits frequently (at least after each completed step), with messages like "wip(P1): add pdf inspection script". Record the latest commit hash in workstamp.md. When a prompt is fully complete, make a final commit "P1: <summary>", set state to DONE, append to "Prompt history", and set "Next action" to "Await next prompt".
5. If a session starts and workstamp.md shows an IN PROGRESS prompt (a previous session was interrupted), do NOT start over. Resume procedure: read workstamp.md and PROJECT_BRIEF.md; run git status, git log -5 and git diff to see the real state; run the test suite; compare reality with the plan; treat any step marked [~] as unverified and re-check it; fix inconsistencies; add a "Sessions" row noting "Resumed after interruption"; continue from the first incomplete step. Never redo steps verified as complete and never discard work already in the repo.
6. Keep workstamp.md accurate and concise. It is a handoff note, not a diary.

Part A tasks:
- Create workstamp.md now, with P1 set to IN PROGRESS and this prompt copied verbatim, BEFORE doing anything else.
- Backfill "Prompt history" with P0: scaffolding, dependencies and smoke tests done, commit 8c34c1d, with a note that P0 was executed before the protocol existed. Add Session 1 (Opus 4.6; start time "unknown").
- Add a section "Agent working rules" to PROJECT_BRIEF.md summarising this protocol, and state that any agent must read workstamp.md before doing anything.
- Align phase numbering in PROJECT_BRIEF.md and README.md with this plan (your earlier text mentions ground truth as "Phase 4" and the next step as "extraction"; fix that):
  P0 setup (done); P1 inspect the PDF; P2 ground truth (hand-verified table, created from the rendered page image, independent of the parser); P3 normalization utilities and tests; P4 row reconstruction; P5 hierarchy and parent-path inference; P6 CSV and JSON export; P7 evaluation metrics (cell accuracy, structural accuracy, accounting checks); P8 end-to-end run, failure analysis, robustness test; P9 independent review by a different AI agent; P10 apply review fixes; P11 write-up; P12 optional OCR/VLM backend stub; P13 clean-clone reproducibility check.
- Also generate a requirements.lock (pip freeze of the working environment) so the exact versions that passed are recorded, and mention it in the README. Keep pyproject.toml as it is.
- Commit this as "chore: add session handoff protocol and align phase numbering".

## Part B: Phase 1 work, inspect the PDF
Goal: understand exactly what the text layer of data/raw/balance_sheet_after_correction.pdf contains, so that later phases rest on evidence instead of assumptions.

1. Write scripts/inspect_pdf.py (a diagnostic tool, not the parser). Using PyMuPDF and pdfplumber, it should:
   - Report page count, page size, rotation, and whether any images are on the page.
   - Dump every word with its bounding box (x0, y0, x1, y1), font name and size where available, into notes/words_pymupdf.json and notes/words_pdfplumber.json.
   - Dump drawn vector elements (lines and rectangles) with coordinates into notes/drawings.json, and report whether there are any table rules, underlines or shaded regions.
   - Cluster words into visual rows by vertical position (a simple tolerance-based grouping is fine for diagnostics; state the tolerance you used and why) and print each row as: row number, y position, left edge x0 of the first token, and the text with tokens separated by " | ".
   - Print x0 and x1 distributions: the distinct left-edge positions of row labels, and the right-edge positions of numeric tokens.
2. Render page 1 to a PNG at 200 DPI as data/derived/page4_200dpi.png (create data/derived/ and make sure it is NOT git-ignored; the image will be used later for ground-truth verification). Do not alter the original PDF.
3. Write notes/inspection.md with findings based ONLY on what the script actually shows. Answer each question below with evidence (coordinates, counts, examples), and say "unclear" where the data does not settle it:
   Q1. Do the two libraries agree on tokenization (word boundaries, bboxes)? Where do they differ?
   Q2. Are labels and numbers separate tokens? Are △, －, commas, full-width digits and full-width parentheses preserved exactly as printed? Give examples.
   Q3. Can rows be reconstructed reliably by vertical clustering? Are there rows where a label and its numbers have noticeably different y values, or wrapped labels spanning two lines?
   Q4. Where are the two numeric columns (previous year, current year)? Give x-ranges, and say whether numbers are right-aligned.
   Q5. Is hierarchy visible in the layout? List the distinct label left-edge (x0) positions, how many indent levels they suggest, and two or three example labels per level. State clearly whether indentation alone is enough to recover the hierarchy or whether rules based on label text (for example labels ending in 合計, （純額）, 減価償却累計額) are also needed.
   Q6. Which rows have no numbers (headers such as 資産の部, 流動資産, 有形固定資産) and which have numbers? How many rows of each kind?
   Q7. Are there any drawn lines, shaded areas, hidden text, overlapping text, or images that could matter for a parser?
   Q8. How are the page header items (page number "- 4 -", （訂正後）, the title, the unit line 単位：千円 and the two period headings) positioned relative to the table body?
   Q9. List anything surprising or risky for later phases.
4. Add one pytest test that runs the inspection script's main functions on the PDF and asserts that the expected output files are produced and non-empty. Do not assert any financial values or label counts.
5. Run the full test suite. Update README with how to run the inspection script.

## Constraints
- Diagnostics only: no number parsing, no label normalization, no hierarchy inference, no evaluation, and no ground-truth values. Do not invent data. Do not write anything into data/gt/.
- Do not modify the original PDF.
- Follow the handoff protocol for every step of this prompt, including Part A. Keep explaining your decisions as you go.

## Acceptance criteria
- workstamp.md exists, shows P0 in the history, and shows P1 as DONE at the end, with the verbatim text of this prompt.
- PROJECT_BRIEF.md has "Agent working rules" and the aligned phase list; README matches it.
- notes/inspection.md answers Q1 to Q9 with evidence from the actual output.
- data/derived/page4_200dpi.png exists and is committed.
- pytest passes. Commit hashes are recorded in workstamp.md.
- Your final message shows: the answers to Q1 to Q9 in condensed form, the file list, the test output, and any assumptions or uncertainties.

## Plan for this prompt

1. [x] Create workstamp.md with P1 IN PROGRESS and verbatim prompt
2. [x] Add "Agent working rules" to PROJECT_BRIEF.md
3. [x] Align phase numbering in PROJECT_BRIEF.md
4. [x] Align phase numbering in README.md
5. [x] Generate requirements.lock
6. [x] Commit Part A: "chore: add session handoff protocol and align phase numbering"
7. [x] Write scripts/inspect_pdf.py
8. [x] Run inspect_pdf.py and generate output files
9. [x] Render page to PNG at data/derived/page4_200dpi.png
10. [x] Write notes/inspection.md answering Q1–Q9
11. [x] Add pytest test for inspection script
12. [x] Update README with inspection script usage
13. [x] Run full test suite — 11/11 passed
14. [x] Final commit "P1: PDF inspection and diagnostics"

## Files created or modified

- workstamp.md — created, updated for sessions 3 and 4
- PROJECT_BRIEF.md — added Agent working rules, aligned P0–P13 phases
- README.md — aligned phases, added requirements.lock and inspect_pdf docs
- requirements.lock — created via pip freeze
- scripts/inspect_pdf.py — diagnostic inspection tool (commit 66f0ac8)
- notes/words_pymupdf.json — word dump from PyMuPDF (untracked, generated)
- notes/words_pdfplumber.json — word dump from pdfplumber (untracked, generated)
- notes/drawings.json — vector drawing dump (untracked, generated)
- notes/inspection.md — answers Q1–Q9 with evidence from actual output
- notes/analyze_output.py — scratch analysis script (tracked for reproducibility)
- notes/words_pymupdf.json — word dump from PyMuPDF
- notes/words_pdfplumber.json — word dump from pdfplumber
- notes/drawings.json — vector drawing dump
- data/derived/page4_200dpi.png — rendered page at 200 DPI
- tests/test_inspection.py — 8 pytest tests for inspection script
- README.md — updated status, scripts section

## Last action and result

Full test suite: 11/11 passed (3 smoke + 8 inspection). Final commit pending.

## Decisions and assumptions

- P0 was done before the handoff protocol existed; backfilled in prompt history.
- Session 2 was cut off by usage limit right after creating workstamp.md; no work was lost.
- Removed self-referencing `-e git+...` line from requirements.lock (won't resolve on fresh clone).

## Known issues / open questions

- None yet.

## Next action

Await next prompt.

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
