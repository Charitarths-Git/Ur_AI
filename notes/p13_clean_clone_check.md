> **2026-10-23 attribution correction (user-supplied):** The owner attributes
> P13 and the original P2–P8 implementation to GPT 6.1 Sol (Codex), P9 review to
> Claude Sonnet 4.6, P10a fixes (5565491, d51c47f) to Gemini Flash 3.8, and the
> P10b audit to the original builder model, GPT 6.1 Sol. Model/tool identity is
> owner-supplied, not independently established by this clean-clone check.
> All test, timing, hash and hygiene observations below remain unchanged.

# P13 clean-clone reproducibility check

## Scope and tested revision

Both temporary clones checked committed **8e61adc3ad927bd3fed9d75cd69ed89864bbcd84**, not the main working directory.
This revision is the P13 orientation/handoff commit after the P11 draft. No ignored/untracked files, existing venv, or main-copy package files were copied into either clone. The second clone was made from the first clone's Git repository, so both used exactly the same commit.
Main started clean at f8e354db44fbaa9942b1764dc45cf7e9b4cc23fc. REPORT.md was never modified, staged, stashed, reverted or committed by this task. Any concurrent human edits are excluded from this committed-state check.
Windows, Python **3.14.0** in both routes. Both fresh venv configurations disable system site-packages. Pip used its normal wheel cache; caches were not imported as working-tree inputs. This does not validate other operating systems/Python versions or offline installation.

## PASS / FAIL table

| Check | Result | Evidence |
|---|---|---|
| Fresh committed clone | PASS | Temporary clones outside project; identical recorded HEAD; initially clean |
| README pyproject install | PASS | python -m venv .venv; documented activation; pip install -e ".[dev]" |
| README requirements.lock install | PASS | Separate clone and fresh .venv; pip install -r requirements.lock; no additional install commands |
| Full tests | PASS | Main 298; editable clone 298; pinned clone 298 |
| Documented Ruff | PASS | All checks passed in both clone environments |
| CSV/JSON exports | PASS | Both environment routes reproduce examples byte for byte/SHA256 |
| Evaluation reports | PASS | All four reports byte-identical to Git blobs in both routes; no numeric, timestamp, path or whitespace differences |
| Tracked protected files/BOM | PASS | Raw PDF, all GT files and page4_200dpi.png tracked/present; CSV BOM retained |
| Ignore rules/tracked generated directories | PASS | All five ignore probes match; no requested venv/cache/output directory tracked |
| Hygiene ready for submission | FAIL | Identifying paths/usernames and email location remain; report-only scan, no redaction |
| Phase/state agreement at cloned revision | FAIL | README status lags workstamp; original brief remains a static plan; README clarified afterward |

## Commands used

The placeholders below mask local directory names. Commands after each cd ran only inside that clone. The environment/install commands were already in the cloned README; no missing install step was bypassed. Python --version and timing/hash/scan probes are requested inspection, not extra installation steps.

```powershell
git clone "<LOCAL_REPO>" "<TEMP_ROOT>\clean_clone"
cd "<TEMP_ROOT>\clean_clone"
$env:PYTHONIOENCODING="utf-8"
python --version
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m ruff check src scripts tests eval
python scripts/parse_page.py data/raw/balance_sheet_after_correction.pdf --page 1 --out-dir outputs
python eval/run_eval.py --pred examples/balance_sheet_after_correction_p1.csv --pred-json examples/balance_sheet_after_correction_p1.json --gt data/gt/page4.csv --gt-meta data/gt/page4_meta.json
python eval/run_robustness.py
```

The independent pinned route used:

```powershell
git clone "<TEMP_ROOT>\clean_clone" "<TEMP_ROOT>\lock_clone"
cd "<TEMP_ROOT>\lock_clone"
$env:PYTHONIOENCODING="utf-8"
python --version
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.lock
# Then the exact same pytest, Ruff, parser, evaluator and robustness commands above.
```

No activation failure or README installation error occurred. The lock route installs dependencies, not the local package, but the documented scripts and tests work from the repository root. The editable alternative installs the local package too.

## Test counts and runtimes

| Environment | Tests | Test seconds | Ruff | Robustness seconds |
|---|---:|---:|---|---:|
| Main baseline | 298 passed | 13.38 | Not rerun in main for this prompt | Not run in main |
| Editable fresh clone | 298 passed | 20.39 | All checks passed (0.17.2) | 20.571 |
| Locked fresh clone | 298 passed | 12.55 | All checks passed (0.17.1) | 18.831 |

Each robustness run completed all 360 seed/amplitude/axis attempts, so none was skipped for runtime. Flexible dependency resolution selected a newer Ruff than the lock; both lint runs passed. No test required copying an ignored/untracked input. Generated temporary fixtures/caches/outputs are expected; both clones had clean tracked Git status after regeneration.

## Byte identity

Read-only verification used Python hashlib.sha256 over regenerated bytes. For exports, reference bytes came from examples/; for each evaluation report, reference bytes came from git show HEAD:<path>. All byte comparisons and hashes agree in both environments. The README evaluator scores examples, not outputs; freshly parsed outputs were checked identical to those examples first.

| Artifact | SHA256 (committed reference = editable = pinned) |
|---|---|
| outputs/balance_sheet_after_correction_p1.csv | 943c9d8a7f200db1438e0d0da023d34615fbe011691a6c06788d6148a01f85b2 |
| outputs/balance_sheet_after_correction_p1.json | 2540ff40c6724bb93a28dd4e65650ec50eb14490b097ed41b3de19912dbab9ab |
| eval/results/page4_report.json | 99e9bf9373c24ace8f3b79ca61f007ae499536b11b2312b94ef41bd8d32aebbb |
| eval/results/page4_report.md | bf7af32b247b2dd54d2f60f42fd4f9b822f9f170c8c7435f383f654558c5225e |
| eval/results/robustness_report.json | 35fda325bb895081ddc226884d59099c1794213691a38d2e0b9047ed3ddf1829 |
| eval/results/robustness_report.md | e3f6ec53356191a8ff9c44d436914e3932115cbdd1221bbc0d9e7147156f1f86 |

Report differences: **none**. There are no acceptable timestamp/path-only exceptions to list, and no numeric differences. The existing duplicate accounting headline in page4_report.md is reproduced exactly and was not repaired.

## Protected tracked assets

Tracking was enumerated with git ls-files. All raw/GT files and the required render were present; the CSV begins with bytes EF BB BF. The pipeline did not change their tracked contents.

| File | SHA256 in clone |
|---|---|
| data/derived/page4_200dpi.png | 42b982b36d2b4cdbcc19ed2d28a2a71a55dd90cfa1ad582d8c2d205b7968fa96 |
| data/gt/.gitkeep | e1438564b655e59e371f5ec529adb21df9c98d997b3d8b70c21754c30817e654 |
| data/gt/README.md | c428b937b8ff3f4193434b5a5c076fdfa204b2cf8b6785dcab6a88f96dcca7bb |
| data/gt/page4.csv | c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835 |
| data/gt/page4_meta.json | 6e21ec3d0d4adc1a016534e1f90f24f9ebc32f795baca2f5afa64a87ec7d66a7 |
| data/raw/balance_sheet_after_correction.pdf | 0764bba6f5f0e7984a837e4cc19d8bb95db4a7ac22c26f18c95bbe652c983c74 |

## Hygiene scan — masked locations only

All 93 tracked files were scanned, including chat_logs, workstamp and seven binary files. Pattern categories covered Windows drive paths, common Unix absolute roots, the local account name, emails, common API-key/token/JWT/private-key formats, and quoted credential assignments. Values are omitted. This is a pattern scan, not proof that no secret exists. No key/token/private-key or credential-assignment pattern was detected.

The table gives line locations in the cloned commit, not values. Binary line numbers refer to decoded byte streams, not rendered page positions. Ranges include every consecutive line in the range.

| File | Category | Line locations | Value |
|---|---|---|---|
| chat_logs/chat_log.md | absolute_windows_path | 1059, 1063, 1078, 1138, 1140, 1143, 1145 | [MASKED] |
| chat_logs/chat_log.md | local_username | 1059, 1063, 1078, 1138, 1140, 1143, 1145 | [MASKED] |
| chat_logs/transcript_full.jsonl | absolute_windows_path | 4, 6–7, 9, 11–25, 27–28, 30, 32, 34–36, 38–41, 43, 45–46, 48, 50, 52, 54–55, 57–58, 61, 63, 65–67, 69, 71–72, 75–76, 79, 84–85, 87–88, 91–92, 94–99, 102–105, 107, 109, 111, 113, 115–119, 121–122, 128–131, 133–134, 136–142, 145, 147, 149–151, 153–159, 161–165, 167–171, 173–175, 177, 184–186, 188, 190–192, 194–196, 198–202, 204–206, 209–215, 217–219, 221–223, 226–228, 232–237, 239–241, 243, 245–247, 249, 251, 253–254, 256–258 | [MASKED] |
| chat_logs/transcript_full.jsonl | local_username | 4, 6–7, 9, 11–25, 27–28, 30, 32, 34–36, 38–41, 43, 45–46, 48, 50, 52, 54–55, 57–58, 61, 63, 65–67, 69, 71–72, 75–76, 79, 84–88, 91–92, 94–99, 102–105, 107, 109, 111, 113, 115–119, 121–122, 128–131, 133–134, 136–142, 145, 147, 149–151, 153–159, 161–165, 167–171, 173–175, 177, 184–186, 188, 190–192, 194–196, 198–202, 204–206, 209–215, 217–219, 221–223, 226–228, 232–237, 239–241, 243, 245–247, 249, 251, 253–254, 256–258 | [MASKED] |
| chat_logs/transcript_full.jsonl | absolute_unix_path | 157 | [MASKED] |
| chat_logs/transcript_full.jsonl | email | 205 | [MASKED] |
| data/derived/crops/body_3_300dpi.png | absolute_windows_path | 2262, 3040 | [MASKED] |
| data/derived/page4_200dpi.png | absolute_windows_path | 4594, 5737 | [MASKED] |
| data/raw/balance_sheet_after_correction.pdf | absolute_windows_path | 266, 2317, 5951 | [MASKED] |
| notes/p2_report.md | absolute_windows_path | 78 | [MASKED] |
| notes/p2_report.md | local_username | 78 | [MASKED] |
| notes/review_P9.md | absolute_windows_path | 39 | [MASKED] |
| notes/review_P9.md | absolute_unix_path | 39 | [MASKED] |
| scripts/export_chat.py | absolute_windows_path | 17 | [MASKED] |
| scripts/export_chat.py | local_username | 17 | [MASKED] |
| scripts/inspect_pdf.py | absolute_unix_path | 1 | [MASKED] |
| workstamp.md | absolute_windows_path | 41 | [MASKED] |

Confirmed review targets include the conversation logs, historical test-output root in notes/p2_report.md:78, and the machine-specific source location in scripts/export_chat.py:17. The email candidate is chat_logs/transcript_full.jsonl:205. No values were printed or copied into this report. The source path helper was not run or changed as part of reproduction.

Some matches are not personal data: notes/review_P9.md:39 and workstamp.md:41 contain example/search path patterns; scripts/inspect_pdf.py:1 is a portable interpreter shebang. Binary candidates are only short printable runs (three to seven characters) around compressed bytes; they are unconfirmed pattern hits, not evidence of an embedded private path. Do not alter protected binary assets on that basis. Human review/redaction remains outstanding for the actual identifying text locations.

Ignore probes (all matched): .venv/probe, nested/__pycache__/probe.pyc, .pytest_cache/probe, .ruff_cache/probe, outputs/probe. No tracked path has any of those generated directory components. The check used NUL-delimited git check-ignore --stdin input to avoid Windows CRLF path quoting.

## Documentation contradictions and fixes

- In the cloned revision README.md:5–6 still says P10b/current and P11/P13 next, while workstamp.md:7–8 records P13 IN PROGRESS and its history records P11 complete. README phase rows 85–89 lag actual completion and omit the additional P10b audit.
- README and PROJECT_BRIEF share the original P0–P13 plan. PROJECT_BRIEF.md:42–59 is explicitly Planned Phases, with only the original setup checkmark; it is not a synchronized completion dashboard. Workstamp is the authoritative live state under its agent rules. README now explains that distinction rather than rewriting the original brief.
- The cloned revision contained conflicting model labels. The owner later supplied the authoritative attribution on 2026-10-23: P9 reviewer Claude Sonnet 4.6; P10a fixer Gemini Flash 3.8; original builder and P10b/P13 auditor GPT 6.1 Sol (Codex). These identities are user-supplied, not a result of the clone test. The dated note on the historical P2 draft now points to the later verified GT record. The owner also identifies Claude as the second AI GT reader; those roles are recorded in workstamp.md.
- No command was missing or wrong for the tested Windows environment. README changes put the existing UTF-8 setting next to setup, clarify the two alternative installation routes, consolidate the already-tested commands, link this evidence, and update stale phase/status text. No code, tests, lockfile, data, eval artifact, examples, threshold or REPORT.md was changed.

## Cleanup and unresolved work

Both temporary clones, both virtual environments and the task-owned temp base were deleted after resolving and checking the exact target boundaries under the system temp directory, outside the project. The base contained only the two expected clone directories; deletion was confined to those targets. No temporary environment is retained as a project dependency. P13 verifies reproducibility only; unresolved work is final human report editing, final chat export, redaction/review of identifying tracked text, addition of the Claude conversation log, and submission. The final export helper itself was not tested here.
