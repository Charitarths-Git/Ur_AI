# Page 4 draft ground truth — human verification

Status: **DRAFT**, not verified by a human. Source: the rendered page and
300 DPI overlapping crops in `data/derived/crops/`. Check each entry against
the image, including the label, signs, commas and nil marks. Parent paths are
in the CSV for separate hierarchy review. Header cells are intentionally blank.

Image-only CSV frozen in commit `7ca2ef8` before any text-layer cross-check.
Uncertain cells: none identified after enlarged visual review. This does not
substitute for human verification. No convention deviations or open questions.

| row_id | label | previous raw | current raw | human check |
|---|---|---|---|---|
| r001 | 資産の部 |  |  | [ ] verified |
| r002 | 流動資産 |  |  | [ ] verified |
| r003 | 現金及び預金 | 2,002,429 | 608,281 | [ ] verified |
| r004 | 受取手形 | 20,659 | 26,333 | [ ] verified |
| r005 | 売掛金 | 2,019,476 | 884,339 | [ ] verified |
| r006 | 電子記録債権 | 564,667 | 370,468 | [ ] verified |
| r007 | 商品及び製品 | 589,488 | 1,019,663 | [ ] verified |
| r008 | 仕掛品 | 186,748 | 55,344 | [ ] verified |
| r009 | 原材料及び貯蔵品 | 370,403 | 136,082 | [ ] verified |
| r010 | 短期貸付金 | 7,530 | 30,000 | [ ] verified |
| r011 | その他 | 105,260 | 246,895 | [ ] verified |
| r012 | 貸倒引当金 | △2,979 | △0 | [ ] verified |
| r013 | 流動資産合計 | 5,863,684 | 3,377,407 | [ ] verified |
| r014 | 固定資産 |  |  | [ ] verified |
| r015 | 有形固定資産 |  |  | [ ] verified |
| r016 | 建物及び構築物 | 2,121,360 | 1,880,082 | [ ] verified |
| r017 | 減価償却累計額 | △1,923,585 | △1,640,253 | [ ] verified |
| r018 | 建物及び構築物（純額） | 197,775 | 239,828 | [ ] verified |
| r019 | 機械装置及び運搬具 | 4,024,922 | 2,250,799 | [ ] verified |
| r020 | 減価償却累計額 | △3,634,165 | △1,914,091 | [ ] verified |
| r021 | 機械装置及び運搬具（純額） | 390,757 | 336,708 | [ ] verified |
| r022 | 土地 | 768,976 | 705,403 | [ ] verified |
| r023 | リース資産 | 210,746 | 213,939 | [ ] verified |
| r024 | 減価償却累計額 | △147,599 | △172,066 | [ ] verified |
| r025 | リース資産（純額） | 63,146 | 41,872 | [ ] verified |
| r026 | 建設仮勘定 | － | 4,553 | [ ] verified |
| r027 | その他 | 848,814 | 446,126 | [ ] verified |
| r028 | 減価償却累計額 | △840,375 | △421,883 | [ ] verified |
| r029 | その他（純額） | 8,439 | 24,243 | [ ] verified |
| r030 | 有形固定資産合計 | 1,429,094 | 1,352,610 | [ ] verified |
| r031 | 無形固定資産 |  |  | [ ] verified |
| r032 | リース資産 | 34,190 | 21,402 | [ ] verified |
| r033 | その他 | 10,070 | 14,466 | [ ] verified |
| r034 | 無形固定資産合計 | 44,261 | 35,869 | [ ] verified |
| r035 | 投資その他の資産 |  |  | [ ] verified |
| r036 | 投資有価証券 | 44,180 | 218,836 | [ ] verified |
| r037 | 関係会社株式 | 1,123 | 1,123 | [ ] verified |
| r038 | 長期貸付金 | － | 62,000 | [ ] verified |
| r039 | 退職給付に係る資産 | 18,404 | 16,435 | [ ] verified |
| r040 | その他 | 133,361 | 70,967 | [ ] verified |
| r041 | 投資その他の資産合計 | 197,069 | 369,362 | [ ] verified |
| r042 | 固定資産合計 | 1,670,426 | 1,757,841 | [ ] verified |
| r043 | 資産合計 | 7,534,110 | 5,135,249 | [ ] verified |

## Additional verification

- [ ] Check page metadata, headings, end dates and footer in `data/gt/page4_meta.json`.
- [ ] Check the semantic parents in the CSV, including gross/contra/net families.
- [ ] Adjudicate any arithmetic differences against the page; do not change values to force sums.
- [ ] Confirm the draft explicitly before changing `verified_by_human` to true or starting P3.
