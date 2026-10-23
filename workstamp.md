# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P11 |
| State | IN PROGRESS |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T11:33:02+00:00 |

## Current prompt (verbatim)

FIRST: Read PROJECT_BRIEF.md ("Agent working rules") and workstamp.md, then run git status, git log -5 and the full test suite (PYTHONIOENCODING=utf-8) and report the real state. Follow the handoff protocol for this prompt: copy this prompt verbatim into workstamp.md, write a numbered plan, set P11 IN PROGRESS, update workstamp.md after every step, and make small commits. Sessions table: if this is a continuation of the current session, do not add a "Resumed in new session" row; only add a row (with your ACTUAL model name) if this is genuinely a new session. If workstamp.md shows an interrupted prompt, follow the resume procedure.

# P11: Write-up draft (docs only, no code changes)
Write REPORT.md at the repo root: the short write-up for a take-home problem (parse a Japanese consolidated balance sheet page into a correct table; define and measure "correct"). Target 900 to 1,400 words plus at most three small tables. I will rewrite it in my own words, so write a clear, plain, honest DRAFT, not marketing. The most important part is how "correct" is defined and measured (section 3), then the honest results and failures.

## Hard rules
- Use ONLY facts and numbers that you read from committed files in this repo: README.md, PROJECT_BRIEF.md, workstamp.md, notes/*.md, eval/results/*, examples/*. Do not use numbers from memory or from this prompt. After each number or claim give the source file in parentheses.
- Never claim generalisation: results are on ONE page, the rules were written after seeing it, and the ground truth was transcribed by an AI agent from the page image, checked by me and a second AI reading, and cross-checked against the PDF text layer. Say so plainly.
- Separate "measured" from "expected but not tested".
- Report regressions as well as improvements. P10 lowered row F1 and parent accuracy at higher noise (see notes/failure_analysis.md). A pitch-based threshold was tried in P10b and rejected; list it as a known limitation, not a success. The y-jitter seed-11 row split remains.
- Describe the process accurately: the independent review (P9) was written by one agent, the fixes (P10) were applied in a different tool and session by the same agent that wrote the review, and P10b (a third session) audited them. Do not call the review "fully independent" beyond what the repo supports.
- Where I must supply a fact only I know, write a visible placeholder such as [USER: who verified the ground truth, and how] and do not invent it. Also leave placeholders for time spent and for a one-paragraph personal reflection.
- If any file contradicts another, list the contradiction in a "Things to check" section at the end of your final message instead of picking one silently.

## Sections
1. Problem and assumptions (born-digital PDF, 千円 units, the output schema I promised: flat CSV plus hierarchical JSON).
2. Approach: pipeline from PDF to words, rows, columns, row types, hierarchy, export; the key design decisions and why (relative geometry instead of absolute coordinates, language rules separated from logic, pluggable backend for a later OCR/VLM path).
3. What "correct" means: the three families of metrics (cell-level against hand-labeled ground truth, structural accuracy, label-free accounting checks with a rounding tolerance), including the rounding tolerance reasoning and the truncation hypothesis labelled as a hypothesis.
4. Results on the supplied page: one table with the headline metrics and denominators, and the accounting check summary.
5. Robustness and failure analysis: jitter sweeps before and after the clustering fix (use the before/after table from the notes), ablations, fault-injection detection by digit position, the main failure modes, and what is still broken.
6. Limitations and next steps: scanned pages and a VLM or OCR backend, multi-page and other statements, learned layout models for hierarchy without indentation, how I would scale evaluation to many PDFs, a held-out set.
7. How I used AI tools: the roles (which tool and model did what), the handoff file used across sessions and usage-limit cutoffs, the review and audit chain described above, human verification steps (placeholders where I must confirm).
8. Reproduce: the exact commands from the README that regenerate the page-4 outputs and the evaluation reports.

## Finish
Do not modify anything except REPORT.md, README.md (a short "Results at a glance" pointer to REPORT.md near the top) and workstamp.md. Commit "docs(P11): draft write-up"; set workstamp.md DONE with "Next action: human rewrite of REPORT.md, then P13 final checks".

Final message: the word count, a list of every placeholder, every claim you could not source, and the "Things to check" list.

## Plan for this prompt

1. [x] Read brief/handoff; inspect Git and full suite; report actual baseline.
2. [~] Read committed permitted sources; map claims and flag contradictory provenance.
3. [ ] Draft REPORT.md, prioritizing correctness definitions, measured failures and placeholders; add short README pointer.
4. [ ] Check word count, tables, citations, exact README commands, placeholders and file scope.
5. [ ] Commit draft and DONE handoff; next human rewrite then P13.

## Files created or modified

- workstamp.md — verbatim corrected P11 prompt, plan and baseline.

## Last action and result

Clean main at6127601; ahead of origin/main by5 commits. No interrupted prompt:
P10b DONE. Full baseline:298 passed in12.51s. This is a continuation of Session5;
no new Sessions row added. Only REPORT.md, README.md pointer and this file may change.

## Decisions and assumptions

Use only committed permitted repository sources (baseline6127601). No code/tests/
reports regeneration in this docs-only prompt. Distinguish measured outcomes from
future proposals. Do not invent tool/model or GT reviewer identity; flag conflicts.

## Known issues / open questions

GT notes say independent second review without identifying AI/model; P2 report
still says DRAFT versus later verified checklist. P9 identifies Claude Sonnet4.6
and GPT-6.1 Sol builder; Sessions says P10 Gemini3.8 Flash and builder GPT-6,
while P10b handoff context says reviewer also applied fixes. Record in final
Things to check and leave visible report placeholders for user confirmation.

## Next action

Finish source mapping and draft the short report.

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | Image-derived GT, 43 rows; now VERIFIED by human with no corrections; 12 tests pass | 0be2cf6 (initial GT); verification: 9805d79 |
| P3 | Pure normalization utilities, 129 new tests; full suite 141 passed; GT unchanged | b41840c |
| P4 | Pure relative row/column/indent reconstruction, GT matched; 166 tests pass | 2582b5d |
| P5-P6 | Typed rows, parent tree, metadata and deterministic exports; 223 tests pass; GT unchanged | 2f6fa06 |
| P7-P8 | Independent file evaluator, label-free accounting, deterministic robustness/fault experiments, failure analysis; 275 tests pass; protected files unchanged | f3dcc47251642cb368bf5f69aab3c82df7ae9534 |
| P9 | Independent review; 2 major + 3 minor + 5 nit findings; all 14 claims verified; 275 tests pass | 1b6d244 |
| P10 | Apply review fixes with user adjustments; gap-based clustering; 283 tests pass | 7f5afbd |

| P10b | Independent audit; coverage/warnings/oracle tests and comparisons; 298 tests pass; nine PASS, geometry item PARTIAL | f535470cbf737c2db70ea81fa13132ea158be44d |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
| 6 | Claude Sonnet 4.6 (Thinking) | 2026-10-23T10:00:00Z | P9 independent review; read-only for src/tests/eval/scripts/data |
| 7 | Gemini 3.8 Flash | 2026-10-23T10:25:00Z | P10 apply review fixes with user adjustments |

