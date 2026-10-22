# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P3 |
| State | IN PROGRESS |
| GT | VERIFIED by human; unchanged/read-only |
| Updated | 2026-10-22T18:55:06Z |

## Current prompt (verbatim)

P3: Normalization utilities with unit tests. Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P3 IN PROGRESS, mark steps [~]/[x] as you go, and make small wip(P3) commits. If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure instead of starting over. Set PYTHONIOENCODING=utf-8 for all commands. Add a Sessions row only if this is a new session.

Goal: small, pure, well-tested normalization functions in src/parser/normalize.py. No PDF access, no row reconstruction, no hierarchy or row-type inference, no evaluation logic, no label-rule config (that is P5), no indent clustering (that is P4). Explain each design decision as you go.

## 1. Number parsing: parse_amount(raw) -> AmountResult
Return a small frozen dataclass with: raw (the input exactly as given), value (int or None), status (one of "ok", "nil", "invalid", "empty"), negative (bool), note (short string, empty if nothing notable). Never return a float, never raise for bad input, and never turn invalid input into 0. Units stay as printed (千円): do NOT multiply by 1000 and do not add a scale parameter.
Required behaviour:
- Strip surrounding whitespace (including full-width space U+3000 and NBSP). Empty or whitespace-only input -> status "empty", value None.
- Apply NFKC for digits, commas and parentheses, so full-width digits "２，００２，４２９" and half-width digits both work. Accept thousands separators "," and full-width "，". Do not validate comma grouping strictly, but note it in "note" if a group is not 3 digits (informational only).
- Negative markers: leading △ (U+25B3), ▲ (U+25B2), ASCII hyphen-minus, U+2212 minus, and U+FF0D (the full-width hyphen-minus). Also parentheses "(123)" or "（123）" meaning negative. "△0" and "▲0" must give value 0 with negative True and note "negative zero printed" (value is the integer 0, status "ok").
- Nil markers: a standalone dash and nothing else: U+FF0D "－", U+2015 "―", U+2014 "—", U+2013 "–", U+2212 "−", U+2010 "‐", U+30FC "ー", ASCII "-", or a run of them, possibly with whitespace -> status "nil", value None. A dash FOLLOWED by digits is a negative number, not nil. Also treat "…" / "･･･" is NOT supported: mark those "invalid".
- Anything else (letters, two numbers, "1.5", "12-3", stray symbols, a double sign "△-5") -> status "invalid", value None, with a short note naming the reason. Decide explicitly how to treat a decimal point and document it (my default: invalid, because this page is in whole 千円).
- Never silently accept a trailing unit such as "千円" or "円"; mark invalid.

## 2. Label helpers (matching only, never for output)
- label_key(label) -> str: NFKC, then remove ALL whitespace (including U+3000), keeping the characters otherwise unchanged. So "建物及び構築物 （純額）" and "建物及び構築物（純額）" give the same key. Document clearly that label_key is for COMPARISON ONLY and that output labels stay exactly as printed, because ground truth keeps the printed form, e.g. full-width （純額）.
- labels_equal(a, b) -> bool: compares label_key values.
- label_key must be idempotent; test that.
- Do NOT add any rule about 合計, （純額）, 減価償却累計額 or any other accounting word. That is P5.

## 3. Period heading helper
- parse_period_end(text) -> tuple[int, int, int] | None: extracts (year, month, day) from strings such as "(2025 年３月 31 日)" or "（２０２６年３月３１日）", handling full-width digits and arbitrary spaces. Return None if it cannot find all three parts. No Japanese-era (和暦) support; mention that as a documented limitation.

## 4. Tests (tests/test_normalize.py)
- Table-driven cases for parse_amount covering at least: plain, comma, full-width digits, full-width comma, △ and ▲, hyphen and U+2212 and U+FF0D negatives, parenthesised negatives (half and full width), △0, ▲0, each nil marker above, runs of dashes, dash with spaces, empty, whitespace-only, "1.5", "12-3", "△-5", "12千円", "abc", and a very long number string. Assert status, value and negative for each.
- label_key and labels_equal cases (space variants, half/full-width parentheses, idempotence) and 3 or 4 parse_period_end cases including a failing one.
- GT round trip (read-only): for every row in data/gt/page4.csv, parse_amount(prev_raw) and parse_amount(curr_raw) must reproduce previous_year_value and current_year_value exactly, with nil raws giving value None and empty header cells giving "empty". Read the CSV with encoding utf-8-sig. NEVER write to data/gt/. This test must not use the PDF.
- Run the complete suite, then ruff (if configured) on the new files.

## 5. Docs
- Update README with a short "normalization" section (what the functions do, the nil vs zero rule, "label_key is for matching only").
- Add a short "Decisions" list to the docstring or to notes/normalization.md (decimal handling, dash handling, negative zero, parentheses).

## Constraints
- Do not touch data/gt/, data/raw/, or the original PDF. Do not add dependencies (stdlib only, unicodedata and re are fine). Do not write extraction, hierarchy or evaluation code.
- Do not weaken a test to make it pass; if a GT row fails, report it instead of editing the GT.
- Final commit "P3: normalization utilities and tests"; workstamp.md set to DONE with "Next action: P4 row reconstruction"; append P3 to the Prompt history with the commit hash.

## Final message must show
Orientation (repo state, test count before P3); the public function signatures; the list of decisions made (especially anything ambiguous); test output with counts; the GT round-trip result; ruff result; files created or modified; commit hashes; open questions.

## Plan for this prompt

1. [x] Orient: inspect package/config/docs, run baseline suite, fingerprint protected data.
2. [x] Implement pure amount, label and period normalization utilities; document decisions.
3. [x] Add table-driven unit tests and read-only GT round-trip coverage; verify targeted tests.
4. [x] Update README, run complete suite then ruff on new files; verify protected data unchanged.
5. [~] Final P3 commit, record hash and DONE handoff; next action P4 row reconstruction.

## Files created or modified

- workstamp.md — verbatim P3 prompt, plan, authorization and orientation state.
- src/parser/normalize.py — frozen AmountResult and four pure public helpers; decisions in module docstring.
- tests/test_normalize.py — 129 table-driven tests, including read-only verified GT round trip.
- README.md — normalization documentation and corrected verified-GT/project status.

## Last action and result

Baseline: clean tree at 9805d79; P2 DONE and GT VERIFIED; 12 passed in 3.05s.
Targeted P3 tests: 129 passed in 0.29s.
Complete suite: 141 passed in 3.47s (Python 3.14.0, pytest 9.1.1, venv).
Then ruff check src/parser/normalize.py tests/test_normalize.py: All checks passed!
git diff --check passes. Verbatim P3 prompt matches the supplied attachment.

Read-only GT round trip: all 43 rows / 86 cells match exactly:
72 ok, 2 nil, 12 empty header cells; no invalid cells or value mismatches.
Every data/gt/ and data/raw/ file has identical SHA-256 before/after work/tests.
CSV SHA-256: c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835.
PDF SHA-256: 0764bba6f5f0e7984a837e4cc19d8bb95db4a7ac22c26f18c95bbe652c983c74.
No dependencies added; pyproject.toml and requirements.lock unchanged.

Progress commits: 3a2434c orientation/plan; d9319f9 implementation;
c99cccb unit tests and verified GT round trip. Final P3 commit next.

## Decisions and assumptions

- Continue existing Session 5; this is the same session/chat, so no new Sessions row.
- P3 is now explicitly authorized. Scope: stdlib-only pure normalization and tests/docs.
- GT and original PDF remain read-only; no new extraction, hierarchy or evaluation logic.
- Set PYTHONIOENCODING=utf-8 for commands.
- Whole 千円 only: decimals and trailing units invalid; preserve raw inputs.
- Standalone listed dash runs (including intervening whitespace) are nil; any
  single listed dash preceding digits is negative. Repeated/mixed signs invalid.
- Allow whitespace after a negative sign and just inside parentheses, but reject
  whitespace splitting digits or comma groups. Parentheses cannot combine with signs.
- Nonempty comma groups of unusual widths accepted with an informational note;
  leading/trailing/repeated commas invalid. First group may have 1–3 digits normally.
- Arbitrarily long integer text parsed in bounded chunks, without changing Python's
  global conversion limits. Non-string amount input is invalid and retained as raw.
- Periods: four-digit Gregorian year, first complete match, calendar validation;
  no era conversion. Label keys receive final NFKC after removing whitespace to
  maintain idempotence across newly adjacent combining characters.

## Known issues / open questions

No open questions or GT failures. Documented choices cover the ambiguous dash,
comma-width, internal-whitespace and period-date cases. Japanese-era dates are
unsupported by design. Root README's stale P2 draft claims were corrected using
the recorded human verification; protected GT files were not edited.

## Next action

Create final P3 commit, then record its hash and DONE status for P4 row reconstruction.

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | Image-derived GT, 43 rows; now VERIFIED by human with no corrections; 12 tests pass | 0be2cf6 (initial GT); verification: 9805d79 |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
