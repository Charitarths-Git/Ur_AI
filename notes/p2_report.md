> **2026-10-23 update:** The GT was subsequently verified by the owner; see
> data/gt/README.md and workstamp.md. Transcription is attributed to GPT 6.1 Sol
> per the owner (**user-supplied**, not independently verifiable from repo records).
> The original draft report below is preserved without revision.

# P2 draft ground-truth report

## Status and provenance

DRAFT — pending human verification. `verified_by_human` is false.
Orientation: clean tree at a46ee03, P1 DONE at 0597652, baseline 11 passed in
2.22s. Added Session 5, GPT-6 (Codex), UTC start 2026-10-22T18:00:38Z;
the exact execution timestamp is recorded in workstamp.md.
P1's stale final-commit-pending text was superseded by verified Git history.

Q6 was corrected from P1 notes only in 9a0e517: 39 numeric rows included
the date heading and footer, leaving 37 numeric body rows and six body headers.
Five other page-level headers are excluded: 43 body + 7 page-level = 50 rows.

Transcription used only the 200 DPI rendered page and five 300 DPI crops.
No text layer, word dumps or P1 notes were accessed during transcription.
The completed CSV was frozen in 7ca2ef81fc11039598a95aae611b8ec9433df90c
before scripts/gt_crosscheck.py was written or any GT text comparison was run.
The draft was not altered after comparison.

Rows: **43**. Types: header 6; line_item 22; contra 5; net 4; subtotal 5; total 1.
Uncertain cells: **none identified** after enlarged visual review.
Convention questions/deviations: **none**. Semantic parents follow the supplied
convention; nil values remain empty/null; signed zero retains raw `△0`.

## Self-check output

Differences are information only. No tolerance, financial pass/fail or automated
correction was applied. Null components remain null and are explicitly listed.

```text
Schema OK (including BOM, enums, paths/levels and empty nil cells).
INFORMATION ONLY: units=千円; diff=sum of present components minus printed value.
Empty nil cells stay null: omitted from known-sum and listed explicitly.
No financial pass/fail decision or tolerance is applied.
row_id | label | previous: sum / printed / diff | current: sum / printed / diff
r013 | 流動資産合計 | 5863681 / 5863684 / -3 | 3377405 / 3377407 / -2
  components=r003,r004,r005,r006,r007,r008,r009,r010,r011,r012
r018 | 建物及び構築物（純額） | 197775 / 197775 / +0 | 239829 / 239828 / +1
  components=r016,r017
r021 | 機械装置及び運搬具（純額） | 390757 / 390757 / +0 | 336708 / 336708 / +0
  components=r019,r020
r025 | リース資産（純額） | 63147 / 63146 / +1 | 41873 / 41872 / +1
  components=r023,r024
r029 | その他（純額） | 8439 / 8439 / +0 | 24243 / 24243 / +0
  components=r027,r028
r030 | 有形固定資産合計 | 1429093 / 1429094 / -1 | 1352607 / 1352610 / -3
  components=r018,r021,r022,r025,r026,r029; null omitted=r026:previous_year_value
r034 | 無形固定資産合計 | 44260 / 44261 / -1 | 35868 / 35869 / -1
  components=r032,r033
r041 | 投資その他の資産合計 | 197068 / 197069 / -1 | 369361 / 369362 / -1
  components=r036,r037,r038,r039,r040; null omitted=r038:previous_year_value
r042 | 固定資産合計 | 1670424 / 1670426 / -2 | 1757841 / 1757841 / +0
  components=r030,r034,r041
r043 | 資産合計 | 7534110 / 7534110 / +0 | 5135248 / 5135249 / -1
  components=r013,r042
```

## Post-commit cross-check output

```text
Read-only text cross-check; image GT committed first in 7ca2ef8.
Rows aligned in vertical reading order independently within each value column.
Only numeric/nil tokens inside the body are considered; dates/footer excluded.
previous: GT cells=37, text numeric/nil tokens=37
current: GT cells=37, text numeric/nil tokens=37
Compared cells: 74 (including nil marks and signed zero).
Disagreements: 0
GT SHA-256 unchanged: c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835
Human adjudication against the rendered image remains required.
```

## Full test-suite output

```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\gagan\Downloads\New folder\project\Ur_AI
configfile: pyproject.toml
testpaths: tests
collected 12 items

tests\test_gt_schema.py .                                                [  8%]
tests\test_inspection.py ........                                        [ 75%]
tests\test_smoke.py ...                                                  [100%]

============================= 12 passed in 1.82s ==============================
```

## Artifacts and next action

- data/gt/README.md: exact conventions and image-only provenance.
- data/gt/page4.csv: 43 body rows, UTF-8 with BOM.
- data/gt/page4_meta.json: page/title/unit/period metadata, human verification false.
- data/derived/crops/: five overlapping 300 DPI visual aids.
- scripts/render_gt_crops.py: reproducible rendering only.
- notes/gt_verification.md: one human checkbox per GT row.
- scripts/gt_selfcheck.py: throwaway schema and informational arithmetic aid.
- scripts/gt_crosscheck.py: read-only numeric token comparison, authored after GT freeze.
- tests/test_gt_schema.py: one schema-only pytest; no financial values or row counts.
- notes/p2_report.md: this report and captured diagnostics.
- README.md, notes/inspection.md and workstamp.md: usage, Q6 correction and handoff.

Original PDF and src/ are unchanged. Human verification of GT, then P3.

New-file lint and `git diff --check` pass. The verbatim P2 handoff text was
checked against the supplied prompt. GT content matches freeze 7ca2ef8;
Git normalizes the working CSV's CRLF line endings to LF in its stored blob.
The SHA-256 printed by the diagnostic refers to working CSV bytes.

Progress commits: 4d98884 orientation; 9a0e517 separate P1 fix; ff2d8e1
conventions/crop renderer; 7ca2ef8 image-derived CSV freeze; 43d8298 verification
aids; 8695260 post-freeze cross-check/documentation. Final P2 commit and the
handoff recording commit can be found in Git history; workstamp.md records
the final P2 commit hash.
