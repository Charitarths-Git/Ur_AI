# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P13 |
| State | IN PROGRESS |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T11:43:56+00:00 |

## Current prompt (verbatim)

FIRST: Read PROJECT_BRIEF.md ("Agent working rules") and workstamp.md, then run git status, git log -5 and the full test suite (PYTHONIOENCODING=utf-8) and report the real state. Follow the handoff protocol: copy this prompt verbatim into workstamp.md, write a numbered plan, set P13 IN PROGRESS, update workstamp.md after every step, make small commits. Sessions table: only add a row (with your ACTUAL model name) if this is genuinely a new session. If workstamp.md shows an interrupted prompt, follow the resume procedure.

IMPORTANT: I may be editing REPORT.md by hand while you work. Do NOT modify, stage, stash, revert or commit REPORT.md. Stage only the specific files you changed (never "git add -A"). If git status shows uncommitted changes you did not make, leave them alone and mention them.

# P13: Clean-clone reproducibility check

Goal: prove that a stranger can reproduce the results from a fresh clone using only the documented commands. Test the COMMITTED state, not my working directory.

## 1. Fresh clone
- Create a temporary directory OUTSIDE the project folder (for example under %TEMP%) and run: git clone <path to this repo> <temp>\clean_clone. Work only inside the clone for steps 2 to 5. Do not copy any untracked or ignored file into it.
- Record the cloned commit hash.

## 2. Environment from the documented commands only
- In the clone, create a new virtual environment and install exactly as README.md says (pyproject install; also test installing from requirements.lock if the README mentions it). Use only the commands written in README.md. If a step is missing or wrong in the README, record it as a finding; fix the README afterwards (step 6), not by improvising silently.
- Set PYTHONIOENCODING=utf-8 as the README says. Report the Python version.

## 3. Tests
- Run the full test suite in the clone. Report the counts and compare with the main working copy (expected: the same number passing). Run ruff if the README documents it.
- Report any test that depends on an ignored or untracked file (that would be a reproducibility bug).

## 4. Regenerate outputs and compare
- Run the documented commands that regenerate the page-4 CSV and JSON exports and the evaluation reports (page-4 report and, if documented, the robustness run).
- Compare the regenerated CSV and JSON with examples/ BYTE FOR BYTE (hash comparison) and report.
- Compare regenerated evaluation reports with the committed ones in eval/results/ and list differences. Distinguish timestamps/paths (acceptable) from numeric differences (a finding). If the robustness run is slow, report its runtime; run it only if the README documents it and it finishes in a reasonable time, otherwise say it was skipped and why.
- Confirm data/raw/ PDF, data/gt/ files and data/derived/page4_200dpi.png are present in the clone (tracked), and that the GT CSV still starts with a UTF-8 BOM.

## 5. Hygiene scan (report only, do not delete or edit anything for this step)
- Search the clone for absolute local paths (for example "C:\\Users", the local username), email addresses, tokens or API-key-like strings, in all tracked files including chat_logs/ and workstamp.md. Report file and line numbers only; do NOT print secrets in full (mask them).
- Check .gitignore covers .venv, __pycache__, .pytest_cache, .ruff_cache and outputs/, and that no such directory is tracked.
- Check that README, PROJECT_BRIEF.md and workstamp.md describe the same phase list and the same final state; list contradictions.

## 6. Fix only documentation gaps
- If the README commands were incomplete or wrong, fix README.md (and only docs). Do not change code, tests, data, eval, examples or any threshold. If the check revealed a CODE or DATA problem, do NOT fix it: report it with evidence and stop.
- Commit as "docs(P13): fix reproduction instructions" only if you changed something. Delete the temporary clone and venv afterwards.

## Finish
- Write notes/p13_clean_clone_check.md with a PASS/FAIL table per check (clone, install, tests, exports byte-identical, reports match, protected files present, hygiene), the commands used, and the findings.
- workstamp.md: P13 DONE with "Next action: final export_chat.py, redaction of chat_logs, add the Claude conversation log, submit". Final commit "P13: clean-clone reproducibility check".

Final message: the cloned commit hash, a PASS/FAIL table, test counts in the clone versus the main copy, byte-identity result, differences in reports, hygiene findings (masked, with file:line), README fixes made, and anything unresolved.

## Plan for this prompt

1. [x] Read brief/handoff; Git status/log and full main-copy baseline; record user-edit boundary.
2. [x] Fresh temporary clone outside project; record commit and test README environment/install paths independently.
3. [x] Run clone tests/lint and documented parser/evaluation/robustness commands; compare committed artifacts/hashes.
4. [x] Scan every tracked file for hygiene locations without printing values; verify ignore rules, protected assets and phase/state consistency.
5. [x] Record PASS/FAIL evidence; fix documentation gaps only, if any; preserve REPORT.md and other user edits.
6. [~] Safely delete verified temporary clone/venvs; final scoped commit and DONE handoff.

## Files created or modified

- notes/p13_clean_clone_check.md — commands, hashes, PASS/FAIL evidence and masked hygiene locations.
- README.md — existing-command clarification, reproduction evidence and current status.
- workstamp.md — verbatim P13 request, plan, baseline and boundaries.

## Last action and result

Evidence note written with complete command list, per-route timings, six common
artifact hashes, protected asset hashes and all masked hygiene line locations.
README instructions already worked: only clarifications/consolidation and stale
phase/status text changed. No executable or data repair required. Final cleanup
pending exact temporary-target boundary checks; staged paths will be explicit.

Both committed-state routes complete: editable298 passed in20.39s, pinned298
passed in12.55s; main baseline298 in13.38s. Ruff clean in both. Robustness20.571s
and18.831s, all360 runs retained. Six generated artifacts byte-identical to
committed references in BOTH environments; no report content/numeric/path/time
changes. Clone status clean. Required assets tracked/present, GT BOM retained.

Reproduction passes; hygiene readiness FAIL (masked identifying text locations),
phase/state agreement at cloned revision FAIL (stale README). No code/data
reproduction problem found; no code/data fixes. README now clarifies existing
working commands and updates stale state; original planned brief left intact.
REPORT.md and all user edits remain excluded from staging/changes.

Both README install routes succeeded in separate fresh .venv directories/clones
at the same committed8e61adc revision. Pinned route tests/lint/regeneration now
running; editable route complete and six artifact hashes identical. Phase scan:
common P0–P13 plan, but README5–6 still saysP10b/nextP11 while committed
workstamp saysP13 IN PROGRESS/P11 DONE; README phase rows85–89 stale and omit
P10b. PROJECT_BRIEF is a static planned list, not a live completion record.
These are documentation findings only. No code/data reproduction failure found.

Fresh editable-install clone tested at8e61adc3ad927bd3fed9d75cd69ed89864bbcd84,
Python3.14.0. README venv/activation/pip install -e ".[dev]" succeeds; fresh clone
298 passed in20.39s and documented Ruff command clean. Documented parse/eval/
robustness commands succeed; robustness20.571s. Both exports and all four reports
SHA256/bytes match committed references exactly; clone git status clean afterward.
Second independent clone of same revision is installing requirements.lock in a
separate fresh .venv; no package reuse from main or editable environment.

Tracked-file hygiene scan completed without printing matches:93 tracked files,
seven binaries included; local paths/usernames and one email location found,
no key/token/private-key or credential-assignment pattern found. All required
ignore samples match; no cache/venv/output directory tracked. Protected PDF/GT/
PNG tracked and present; GT BOM retained. Locations/details will be in check note.

Main clean atf8e354d; ahead of origin/main by8 commits. Baseline298 passed in13.38s.
P11 DONE; no interrupted prompt. Current chat continues Session5; no Sessions row.
No uncommitted user changes at orientation; recheck throughout. REPORT.md must
never be modified, staged, stashed, reverted or committed by this task.

## Decisions and assumptions

Clone committed HEAD after this handoff record, not the working directory.
No untracked/ignored files copied. Separate clean venv for each README install
route. Steps2–5 execute inside clone only. Hygiene scan outputs file:line/category,
never full matching values. Only docs may change in main; code/data failures
must be recorded without repair. Stage only named files this task changed.

## Known issues / open questions

Pending clean-clone evidence. Existing report/model provenance contradictions
and the historical GT draft note remain; do not resolve facts by inventing them.

## Next action

Create temporary clone, record its revision, test README commands verbatim.

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

| P11 | Sourced draft REPORT.md;1156 words, three tables, five placeholders; README pointer; docs-only baseline298 tests pass | 2ee75d2 (draft content); final completion commit named docs(P11): draft write-up |

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

