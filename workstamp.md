# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | housekeeping |
| State | IN PROGRESS |
| Last numbered prompt | P13 DONE |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-23T12:14:23+00:00 |

## Current prompt (verbatim except personal-path redaction)

Docs and logs only. Do not touch code logic, tests, data/, eval/, examples/ or any threshold. Set PYTHONIOENCODING=utf-8. Record this under "housekeeping" in workstamp.md's Prompt history, not as a new numbered prompt. Never print a full secret, email or username in your messages; mask them. Stage only files you changed (never "git add -A", never .venv or ignored files). Never force-push and do not change the remote configuration.

A. REPORT.md placeholders
1. Replace [USER: total time spent, including human verification] with this exact text: "Time spent: about two days of elapsed time (Wed 21 to Fri 23 Oct 2026), mostly agent runtime plus my own planning, prompt drafting and manual verification of the ground truth. I did not keep a precise log, so this is an estimate."
2. Replace [USER: one-paragraph personal reflection] with a first-person paragraph of 4 to 6 sentences using ONLY facts already in this repo (REPORT.md, notes/, workstamp.md): that accounting checks caught what cell metrics cannot (printed totals differing from component sums by small rounding amounts), that the jitter sweeps exposed real failures and that the P10 fixes also caused regressions at higher noise, that the pitch-threshold attempt was rejected, that everything is measured on one page with rules written after seeing it, and that the next step would be held-out pages and an OCR/VLM backend. Do not invent feelings, hours or anecdotes. Mark the paragraph's first line with an HTML comment <!-- drafted by agent from repo facts; owner may edit -->.
3. Confirm no "[USER:" text remains in REPORT.md. The only remaining placeholder allowed is none.

B. Wording fixes
In README.md lines 392 and 405, notes/evaluation_design.md lines 24 and 268, and notes/p10_audit.md line 1, replace unqualified "independent audit" with "audit by the builder model (GPT 6.1 Sol), which is weaker independence than a human audit". Change nothing else there. Leave notes/p2_report.md:12 and chat_logs/transcript_full.jsonl:226 as they are (historical).

C. Redaction
1. Using notes/p13_clean_clone_check.md as the starting list, search ALL tracked files (git ls-files) and chat_logs/claude_conversation.md if it exists for: the local Windows username, absolute local paths (<path>, drive-letter paths), email addresses (including any student email or roll number), and token or API-key-like strings.
2. Replace username with <user>, absolute local paths with <path> (keep the repo-relative part), emails with <email>. Cover chat_logs/chat_log.md, chat_logs/transcript_full.jsonl, chat_logs/claude_conversation.md (if present), notes/p2_report.md, notes/p13_clean_clone_check.md, scripts/export_chat.py, workstamp.md, REPORT.md and any other tracked file the search finds. Keep public references (example.com, the Ur AI company name, GitHub URLs, the repo URL github.com/Charitarths-Git/Ur_AI).
3. transcript_full.jsonl: after redaction verify every line parses as JSON. If it cannot be redacted cleanly, delete it, keep chat_log.md only, and update README, workstamp.md and scripts/export_chat.py so they stop mentioning it.
4. scripts/export_chat.py: make it redact username, absolute paths and emails automatically on output; otherwise unchanged behaviour.
5. Do not modify data/raw/, data/gt/, data/derived/, examples/ or eval/results/. If a finding is inside one, report file:line and leave it.
6. Re-run the search and show counts per file (masked); expect zero username, email and absolute-path matches outside the protected files.

D. Verify, commit, push
1. Run the full test suite (expect 298 passed) and git status.
2. Commit as "chore: finalize report text and redact personal info".
3. Run "git push -u origin main". If it fails (authentication, network, non-fast-forward), stop and report the exact error with no workaround.
4. After success show "git status -sb", "git log --oneline -3", and confirm local and remote HEAD match with "git ls-remote origin main".
5. Check README.md and REPORT.md render sensibly: report their first 15 lines.

Final message: files changed, whether transcript_full.jsonl was kept or deleted, remaining matches (masked, file:line), test count, commit hash, push result with local versus remote hash, and anything you could not do.

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

1. [x] Read handoff and Git state; record this housekeeping request. Existing untracked Claude conversation is authorized for scanning/redaction; no other changes found.
2. [x] Complete report placeholders and exact audit wording; scan all tracked files plus Claude log, redact identifying text, add export-output redaction, validate JSONL and rescan.
3. [~] Run full tests; verify protected hashes and scope; inspect README/report previews; commit only changed files.
4. [ ] Push main once as requested; stop on failure; otherwise compare local/remote HEAD and report final status.

## Files created or modified

Pending scope verification. Only documentation, conversation logs and the explicitly requested export-output sanitizer may change.

## Last action and result

Step 2: exact owner time estimate inserted, five factual first-person reflection sentences added with required HTML marker, no REPORT.md USER placeholders remain. Five targeted audit-wording replacements made; historical attribution labels retained. Scanned all tracked files plus existing Claude conversation. Redacted JSON string values recursively, preserving JSONL syntax; public GitHub references retained. Added export-output sanitization and removed literal personal default path (same home-relative source). Initial token/private-key/credential patterns: none. Rescan: 95 files, zero identifying text/key/credential matches outside protected files. Remaining seven compressed-binary path-pattern candidates are unchanged. JSONL retained (258 valid lines). Ruff on export helper passed; synthetic export/full-suite verification follows with normal temp access.

Clean tracked main at7185d4c; existing untracked chat_logs/claude_conversation.md will be inspected under this request. P13 remains DONE; no new numbered prompt or session row. Current request overrides earlier restrictions on redacting historical paths. Protected data/eval/examples/tests/parser logic remain read-only.

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

| housekeeping | Final report text and personal-information redaction IN PROGRESS; existing Claude conversation included in authorized scan | pending |

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
