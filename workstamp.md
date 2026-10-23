# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | housekeeping |
| State | DONE |
| Last numbered prompt | P13 DONE |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T12:14:23+00:00 |

## Current prompt (verbatim)

Docs only. Do not touch code, tests, data, eval, examples or any threshold. Stage only the files you change (never "git add -A"). Set PYTHONIOENCODING=utf-8. Follow the handoff protocol (update workstamp.md, small commits); record this under "housekeeping" in the Prompt history, not as a new numbered prompt. If git status shows uncommitted changes you did not make, leave them alone and mention them.

The owner supplied this authoritative attribution (user-supplied, not verifiable from the repo):
- Implementation plan and prompt drafting: Claude (web, separate account), later a Claude conversation that also gave a second AI reading of the GT transcription and reviewed prompts and results.
- P0, P1: Claude Opus 4.6
- P2 to P8 and P10b to P13: GPT 6.1 Sol (Codex)
- P9 independent review: Claude Sonnet 4.6
- P10a fixes (commits 5565491 and d51c47f): Gemini Flash 3.8
- The P10b audit was done by GPT 6.1 Sol, which also built the original code.

Tasks:
1. workstamp.md: correct the Sessions table and handoff text to match this attribution, marking it "user-supplied". Remove any statement that the reviewer applied the fixes and any "GPT-6" naming that conflicts with "GPT 6.1 Sol". Leave the P13 "Next action" line unchanged.
2. Add a dated note at the top of notes/p2_report.md saying the GT was later verified (see data/gt/README.md and workstamp.md). Do not rewrite the rest.
3. Add a short dated note at the top of notes/review_P9.md saying the reviewer was Claude Sonnet 4.6 per the owner. Do not edit its findings.
4. Correct conflicting attribution in notes/p13_clean_clone_check.md and the P13 entries in workstamp.md.
5. REPORT.md: you may edit it now (I am no longer editing it). Fix section 7 so it matches the attribution above: the review model (Claude Sonnet 4.6) differs from the builder (GPT 6.1 Sol), the fixes were applied by a third model (Gemini Flash 3.8), and the fixes were then audited by the builder model, which is weaker independence than a human audit. Fill the placeholders as follows, and leave a visible [USER: ...] marker only for facts you cannot know:
   - GT verification: transcribed by an AI agent (GPT 6.1 Sol) from the page image, checked row by row by the owner, second AI reading by Claude, cross-checked against the PDF text layer (74 of 74 cells agreed, per notes/p2_report.md or workstamp.md; verify the number in the repo).
   - Rounding/truncation: keep it labelled as an unconfirmed hypothesis.
   - Time spent and personal reflection: keep as [USER: ...] placeholders.
   Verify every number in REPORT.md against its cited file and fix any mismatch; list each correction you made. Keep the honest points: one page only, rules written after seeing it, P10 regressions, the rejected pitch threshold, the remaining seed-11 split.
6. Run the full test suite and git status.

Commit as "docs: correct attribution and finalize report draft".

Final message: files changed, commit hash, test count, git status, corrections made to REPORT.md numbers, remaining [USER: ...] placeholders, and any conflicting attributions found elsewhere (file:line).

## Authoritative attribution — user-supplied (2026-10-23)

The owner supplied the following account. These model/tool identities and human
roles are user-supplied and cannot be independently established from repo files.
They supersede earlier conflicting model labels and role descriptions; numerical
experiment and test records are unchanged.

- Implementation plan and prompt drafting: Claude on the web, separate account.
  A later Claude conversation provided a second AI reading of GT transcription
  and reviewed prompts and results.
- P0–P1: Claude Opus 4.6.
- P2–P8 and P10b–P13: GPT 6.1 Sol (Codex).
- P9 review: Claude Sonnet 4.6, distinct from the builder model.
- P10a fixes: Gemini Flash 3.8 (5565491 and d51c47f), a third model.
- P10b audit: GPT 6.1 Sol, the original builder model. This is a builder-model
  audit of another model's fixes, with weaker independence than a human audit.
- GT: GPT 6.1 Sol transcribed the image; the owner checked every row; Claude
  provided the second AI reading. Repo evidence independently records74 cells
  compared with the PDF text layer and zero disagreements (notes/p2_report.md).

## Plan for this housekeeping

1. [x] Read brief/handoff and Git state; record owner-supplied attribution and preserve P13 next action.
2. [x] Correct only requested docs; prepend dated notes without rewriting historical P2/review bodies.
3. [x] Verify every report number against cited artifacts, list corrections and residual attribution wording elsewhere.
4. [x] Full suite, scope/status checks and final named documentation commit; mark housekeeping DONE.

## Files created or modified

- REPORT.md — owner-supplied GT/tool roles; builder-model audit caveat; unconfirmed policy and two owner-only placeholders.
- notes/p2_report.md — dated verification/attribution note only; original body preserved.
- notes/review_P9.md — dated owner attribution note only; original findings preserved.
- notes/p13_clean_clone_check.md — dated owner attribution correction; reproduction measurements unchanged.
- workstamp.md — housekeeping request, plan, user-supplied attribution and corrected session/phase records.

## Last action and result

Housekeeping DONE: full suite298 passed in11.93s; git diff --check clean.
Only REPORT.md, notes/p2_report.md, notes/review_P9.md,
notes/p13_clean_clone_check.md and workstamp.md changed. No pre-existing or
unrelated user changes observed; no code/tests/data/eval/examples changes.
Dated P2/review notes preserve their original bodies/findings. All attribution
corrections are explicitly owner/user-supplied, not claimed repo verification.
REPORT.md numerical audit found no measured mismatches; added verified74/74
text-layer agreement and corrected model/role labels. Remaining USER markers:
time spent including human verification; one-paragraph personal reflection.
Filing policy still unconfirmed; all honest limits/regressions preserved.
P13 Next action remains byte-for-byte unchanged. No new numbered prompt/session.
Plan commitf8b54d3; final commit named docs: correct attribution and finalize report draft.

All REPORT.md numbers checked against cited files/artifacts: metric numerators/
denominators, seven exact/thirteen within-tolerance/two N/A checks, residuals
-1..+3,20/20 truncation consistency, both1.000000 accounting fractions,20 seeds/
360 attempts, all four before/after mean-min rows,90 assignment cases, seed11
at.2H,38/43 and14/43 ablation results,72/72 coverage and249/648,621/639,3007/3025
digit detection ratios, and0.5/max(1,n)/n+1 method constants. No measured numeric
mismatches found or changed. Added74/74 text-layer agreement from compared74,
disagreements0. Model/version labels corrected from owner attribution, not
inferred from metrics. REPORT.md now1208 words with only time/reflection markers.
P13 next action unchanged. Original P2/review bodies match their prior versions.

Remaining historical names: notes/p2_report.md:12 (preserved historical label;
new note supersedes it); chat_logs/transcript_full.jsonl:226 (legacy model name).
Unqualified audit-independence wording remains in README.md:392,405;
notes/evaluation_design.md:24,268; notes/p10_audit.md:1. Report these locations,
without changing unrequested docs/logs. Full suite/scope check now running.

Requested doc corrections written. Historical P2/review bodies preserved byte-for-
byte beneath dated notes. Report now attributes planning/second reading to Claude,
implementation/audit to GPT 6.1 Sol (Codex), review to Claude Sonnet 4.6, fixes to
Gemini Flash 3.8; all marked owner/user-supplied. P13 attribution corrected without
changing measurements. GT cross-check74/74 added from compared74/disagreements0.
Rounding remains unconfirmed; only time/reflection USER placeholders remain.
Numeric and residual-conflict audit in progress; no protected files changed.

Clean main at97cfb11; no pre-existing uncommitted changes. P13 DONE. Attribution
comes from the owner, not a fresh forensic inference. Current chat continues;
no new runtime-session row. Only the five requested documentation files may change.

## P13 handoff record — attribution corrected, measurements retained

P13 was performed by GPT 6.1 Sol (Codex), per owner (user-supplied). Tested commit
8e61adc3ad927bd3fed9d75cd69ed89864bbcd84 on Windows/Python3.14.0: main298 tests,
editable clone298 in20.39s, locked clone298 in12.55s; both Ruff clean. Robustness
runs20.571s/18.831s. Six generated artifacts were byte-identical in both clones;
protected files tracked/present and GT BOM retained. Temporary clones/venvs removed.
Hygiene redaction remains. P13 did not modify REPORT.md; this later housekeeping
prompt now authorizes report edits. P13 final commit97cfb11; evidenceb178e09;
README9911ca7. No numerical record or protected artifact changed here.

## Decisions and assumptions

Owner-supplied historical attribution supersedes stale labels, without claiming
independent verification from logs. P2/review original bodies must remain intact.
Do not alter code/tests/data/eval/examples/thresholds or unrelated user changes.
Retain one-page development caveats, regressions and known failures in the draft.

## Known issues / open questions

Rounding/truncation policy remains unconfirmed; time and personal reflection are
owner-only facts. Existing identifying tracked text still needs redaction under
P13's unchanged next action. Scan/report remaining historical attribution elsewhere;
do not edit unrequested sources or conversation logs.

## Next action

final export_chat.py, redaction of chat_logs, add the Claude conversation log, submit

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
| P10a (formerly P10 fixes) | Gemini Flash 3.8 fixes (user-supplied); gap clustering; later suite283 at7f5afbd | 5565491; d51c47f; 7f5afbd (later test) |

| P10b | Builder-model audit by GPT 6.1 Sol (user-supplied); coverage/warnings/oracle tests and comparisons; 298 tests pass; nine PASS, geometry item PARTIAL | f535470cbf737c2db70ea81fa13132ea158be44d |

| P11 | Sourced draft REPORT.md;1156 words, three tables, five placeholders; README pointer; docs-only baseline298 tests pass | 2ee75d2 (draft content); final completion commit named docs(P11): draft write-up |

| P13 | GPT 6.1 Sol (Codex), user-supplied; fresh committed clones; both README install paths pass 298 tests/Ruff, exports and reports byte-identical; hygiene redaction pending; temporary envs removed | b178e09 (evidence); 9911ca7 (README); final completion commit named P13: clean-clone reproducibility check |

| housekeeping | User-supplied attribution corrected in five docs; report numbers verified,74/74 text agreement added; two placeholders remain;298 tests pass | f8b54d3 (plan); final commit named docs: correct attribution and finalize report draft |

## Sessions

Model/phase attribution below is **user-supplied**. Historical UTC starts and
usage-limit notes are retained as historical records, not newly verified facts.
No new runtime session is asserted by this housekeeping update.

| # | Model (user-supplied) | UTC start | Note |
|---|---|---|---|
| External | Claude (web, separate account) | unknown | Owner's planning/prompt drafting; later Claude conversation: second AI GT reading and prompt/result review |
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | P1 inspection outputs; cut off before updating workstamp |
| 4 | Claude Opus 4.6 | 2026-10-22T14:19Z | Historical P1 continuation after usage-limit interruption; phase/model mapping corrected per owner |
| 5 | GPT 6.1 Sol (Codex) | 2026-10-22T18:00:38Z | P2–P8 implementation; P10b builder-model audit; P11 draft and P13 clean-clone check |
| 6 | Claude Sonnet 4.6 | 2026-10-23T10:00:00Z | P9 review, read-only for source/tests/eval/scripts/data |
| 7 | Gemini Flash 3.8 | 2026-10-23T10:25:00Z | P10a fixes in5565491 and handoffd51c47f; not the review model |
