# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P5-P6 |
| State | IN PROGRESS |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-22T22:34:55Z |

## Current prompt (verbatim)

P5-P6: Row types, hierarchy and parent paths, page metadata, and CSV/JSON export. Follow the handoff protocol in PROJECT_BRIEF.md "Agent working rules": read PROJECT_BRIEF.md and workstamp.md first, copy this prompt verbatim into "Current prompt (verbatim)" in workstamp.md, write the numbered plan, set P5-P6 IN PROGRESS, mark steps [~]/[x] as you go, and make small wip(P5-P6) commits (at least one per numbered section below). If workstamp.md shows an interrupted IN PROGRESS prompt, follow the resume procedure instead of starting over. If this is a new session (you have no memory of earlier chats): first run git status, git log -5 and the full test suite, report the real state, and add a Sessions row with your actual model name. Set PYTHONIOENCODING=utf-8 for all commands. Explain each design decision as you go.

## Goal
Turn the PageLayout from P4 into the two deliverables I promised: a flat CSV and a hierarchical JSON. Pipeline: PDF -> RawPage (P4 backend) -> PageLayout (P4) -> typed rows and tree (P5) -> files (P6). The algorithm must be general: language-specific words live in a replaceable RuleSet, not in the logic, and the logic must not use data/gt/ or any page-4-specific numbers. Scope limits: NO evaluation metrics module (that is P7), no OCR/VLM backend.

## 1. Small fixes first (separate commits)
a) notes/inspection.md Q5 says there are 4 indent levels; P4 found 5 indent steps (centres about 62.3, 75.2, 88.2, 101.3, 114.2 pt), the first being the root label. Correct that paragraph with evidence.
b) P4 attached the unit line "（単位：千円）" to the heading of the right-hand column. Handle this where you judge cleanest (a minimal fix in rows.py with a regression test, or in the new metadata step) so that column headings no longer contain unit lines. Keep all P4 tests passing and do not weaken any.

## 2. RuleSet (src/parser/rules.py)
A frozen dataclass of language-specific patterns, plus one default instance for Japanese financial statements, e.g. JA_FINANCIAL_STATEMENT. All matching uses label_key from normalize.py; output labels stay exactly as printed.
- total_labels (exact label_key matches or suffix patterns): 資産合計, 負債純資産合計, 負債及び純資産合計, 負債・純資産合計.
- subtotal_suffixes: 合計.
- net_suffixes: （純額） and (純額), compared after label_key normalisation.
- contra_labels (prefix or exact): 減価償却累計額, 貸倒引当金, 自己株式.
- unit patterns: a regex for lines such as （単位：千円）, with a map {千円: 1000, 百万円: 1000000, 円: 1}.
- correction markers: （訂正後）, （訂正前）.
- page number pattern for "- 4 -".
Document in notes/hierarchy_and_export.md that ONLY page 4 has been validated; every other pattern (liabilities, equity, 自己株式, other units) is an untested heuristic. Do not claim more.

## 3. Row types (src/parser/classify.py)
Row types (exactly these, matching the GT convention in data/gt/README.md): header, line_item, contra, net, subtotal, total.
- Decide in this order: no value cells -> header; label matches total_labels -> total; matches net_suffixes -> net; matches subtotal_suffixes -> subtotal; matches contra_labels -> contra; otherwise structural fallback: all numeric cells printed negative (AmountResult.negative, which includes the printed negative zero) -> contra; else line_item.
- Compute structural evidence for every row regardless of the label rule: rule_above, all-negative-cells, no-cells. Emit a typed warning (not an override) when the label-rule type and the evidence disagree: a subtotal, net or total row without a rule above; a contra row without negative cells; a header row with a rule above is NOT a warning (the real page has 4 such headers), but report the counts in the notes.
- Each row records "type_source": "label_rule" or "structural", and the warnings list.

## 4. Hierarchy (src/parser/hierarchy.py)
- Primary method: a parent stack on indent_step. parent = the nearest preceding body row with a strictly smaller indent_step; level = number of ancestors in the resulting tree (do NOT copy the indent step into level). Emit warnings for the first row not being the least indented, and for a jump of more than one indent step.
- Indentation is informative only if the body rows have at least 2 distinct indent steps. Otherwise use a documented, deliberately partial fallback and set hierarchy_source = "rules_fallback" with a warning: header rows attach to the root (their nesting is unknown, say so), line_item and subtotal rows attach to the most recent header, contra and net rows attach to the nearest preceding line_item, total rows attach to the root. Keep this small and clearly labelled partial.
- Output: for each body row: row_id (1-based among body rows, reading order), parent_row_id, parent label, parent_path (ancestor labels joined by " > ", root first), level, children. Build an explicit tree.
- Never read data/gt/ here.

## 5. Page metadata and column roles (src/parser/metadata.py)
- From the header and footer zones, using the RuleSet: title lines, correction marker, unit string and multiplier, printed page number; each None when not found, never guessed.
- Column roles: if there are exactly two columns with distinct period_end values, the earlier is "previous_year" and the later "current_year". Otherwise roles are "value_1".."value_N" (left to right) with a warning. Headings are the cleaned heading text per column.
- Do not multiply values: they stay in the printed unit (千円), as in the GT. Record unit and unit_multiplier as metadata only.

## 6. Export (src/parser/export.py) and CLI
- parse_page(path, page_number=1, layout_config=LayoutConfig(), rules=JA_FINANCIAL_STATEMENT) -> ParsedPage (frozen dataclasses holding rows, tree, metadata, warnings, hierarchy_source). Pure functions below it; the only PDF access is the P4 backend.
- Flat CSV, UTF-8 with BOM, header exactly in this order: label, parent, level, row_type, previous_year_value, current_year_value, row_id, parent_row_id, parent_path, prev_raw, curr_raw. (The first six are the columns I promised; the rest match the GT file names.) Nil cells and header rows have empty values; raw strings are exactly as printed. If the roles are not previous/current, name the value columns value_1..value_N and the raw columns raw_1..raw_N.
- Hierarchical JSON, UTF-8, ensure_ascii=False, indent=2: {"schema_version": "1.0", "source": {file name only, page, backend}, "page": {title, correction_marker, unit, unit_multiplier, printed_page_number}, "columns": [{index, role, heading, period_end as ISO date or null}], "hierarchy_source", "warnings": [...], "rows": [tree nodes]} where a node is {row_id, label, row_type, level, values: {role: {raw, value, status}}, children: [...]}. The tree follows the same convention as the GT: subtotal rows are children of the section they close; contra and net rows are children of their gross item. Deterministic output (stable key order, no timestamps, no absolute paths).
- scripts/parse_page.py PDF [--page N] [--out-dir DIR]: writes <stem>_p<N>.csv and .json; prints a short summary (rows per type, hierarchy source, warnings). Must run without PYTHONIOENCODING set.
- Commit the generated sample outputs for the real page to examples/ (balance_sheet_after_correction_p1.csv and .json); keep outputs/ git-ignored.

## 7. Tests
- Unit tests on synthetic PageLayouts (no PDF): stack parents (siblings, deeper, shallower, first row), skipped-indent warning, flat-indent fallback, each row-type rule and the structural fallback, evidence-conflict warnings, an unlabeled value row, empty body, column roles (two columns, one column, three columns, missing dates), unit parsing for 千円, 百万円 and missing.
- Integration test on data/raw/balance_sheet_after_correction.pdf compared READ-ONLY with data/gt/page4.csv and page4_meta.json (utf-8-sig): for all 43 rows in order, exact label, parent label, parent_row_id, parent_path, level, row_type, previous and current values and raw strings; metadata unit, correction marker, printed page number and the column periods equal the GT meta; hierarchy_source == "indentation"; and report whether the warnings list is empty (my expectation: empty; if not, show it and explain, do not hide it).
- Pipeline invariance: shuffling words, translating, scaling, and small jitter of the real page (reuse the P4 helpers) must give byte-identical CSV and JSON.
- Ablation (not an accuracy claim): flatten the indentation of the real page by moving each row's label tokens to the same x0, then run the pipeline. Assert only: no crash, hierarchy_source == "rules_fallback", a warning is present, row types and values equal the GT. REPORT in the notes how many of the 43 parents the fallback gets right and which kinds of rows it gets wrong.
- Export tests: the CSV column order and BOM; the JSON tree flattened equals the CSV rows; nil gives empty in the CSV and null in the JSON; an invalid cell keeps its status; the output is deterministic.
- CLI subprocess test with PYTHONIOENCODING and PYTHONUTF8 removed from the environment; test that the committed examples/ files equal a fresh generation.
- Run the full suite and ruff.

## 8. Docs
Update README (pipeline overview, how to run parse_page.py, the CSV and JSON schema). Write notes/hierarchy_and_export.md: algorithm, the RuleSet table with each pattern's validation status (validated on page 4 or untested heuristic), the evidence cross-tab (rule_above and negative cells against row types) as counts, the ablation result, design decisions, and a "Known limitations" list (hierarchy without indentation, subtotals without keywords, tables spanning pages, label-less rows, pages with several tables, non-Japanese statements, scanned pages).

## Constraints
- Do not modify data/gt/, data/raw/ or the PDF. Stdlib and pymupdf only. Do not weaken a test to make it pass; if a GT comparison fails, report it and investigate the algorithm; never edit the GT.
- Final commit "P5-P6: row types, hierarchy, metadata, CSV/JSON export"; set workstamp.md to DONE with "Next action: P7-P8 evaluation framework"; append P5-P6 to the Prompt history with the commit hash.

## Final message must show
Orientation (repo state, test count before this prompt); the public API; the RuleSet; the GT comparison result for the real page (how many of 43 rows match on each field); the warnings on the real page; the evidence counts; the ablation result; invariance results; the first 12 lines of the generated CSV; test and ruff output; files created or modified; commit hashes; known limitations; open questions.

## Plan for this prompt

1. [x] Orient, baseline tests and fingerprints; separately fix Q5 and unit-heading metadata cleanup.
2. [x] Implement immutable replaceable RuleSet; commit section 2.
3. [x] Implement pure row classification, evidence and typed warnings; commit section 3.
4. [x] Implement indent-stack tree and partial flat fallback; commit section 4.
5. [x] Extract metadata and date-based column roles, with clean headings; commit section 5.
6. [x] Implement pure parsing pipeline/export serialization, CLI and committed examples; commit section 6.
7. [~] Add synthetic, real GT, byte-invariance, ablation/export/CLI/example tests; commit section 7.
8. [ ] Document patterns, evidence counts, ablation, schemas and limitations; commit section 8.
9. [ ] Full suite then ruff; integrity checks; final commit and DONE handoff.

## Files created or modified

- workstamp.md — P5-P6 verbatim prompt, plan and orientation.

## Last action and result

Section 6 pipeline/serializers/CLI smoke run succeeded: generated both required
examples, 43 rows with expected types, indentation source, zero warnings.
Stable LF example attributes added for byte-identical fresh-clone comparisons.
Hierarchy commit 4cb6d06; metadata commit eeded2a.

Metadata smoke run: two title lines; marker 訂正後; unit 千円, multiplier1000;
printed page4; chronological previous/current roles; unit lines absent from
metadata headings. No metadata warnings. No scaling of values.

Hierarchy smoke run: 43 rows, one tree root, indentation source, no warnings.
Gross item children are its contra and net rows. Levels count ancestor IDs.

Classification smoke run: header=6,line_item=22,contra=5,net=4,subtotal=5,total=1;
warnings empty. Evidence computed independently for every row. RuleSet commit 93ecd54; classification commit 712c2b1.

Section 2 RuleSet smoke checks passed: normalized matching and immutable unit map.
Separate fixes: d28504f Q5; e00ca2f unit-line cleanup helper/regression.

Unit-heading cleanup helper added in metadata.py; regression test passes (1).
It takes a caller-supplied pattern; RuleSet will supply the production pattern.
P4 layout/API and tests are unchanged. Q5 fix commit recorded in Git history.

Baseline 166 passed in 6.73s; protected data fingerprinted. Corrected Q5 and
summary: five body indent steps including root, with P4 centre evidence.

Read brief and handoff; tree clean at 9012bae; P4 DONE, previous full suite 166 passed.
Existing Session 5 continues. No repository AGENTS.md found; no interrupted phase.

## Decisions and assumptions

- GT and raw data read-only. No evaluation metrics or OCR/VLM implementation.
- Language-specific strings/patterns live only in RuleSet, using P3 label_key.
- Address unit-heading contamination in new metadata, leaving pure P4 unchanged.
- Continue Session 5; no new session row. Commands use PYTHONIOENCODING=utf-8.

## Known issues / open questions

Q5 indent-count statement and unit-line contamination will be fixed separately.

## Next action

Add synthetic/GT/invariance/ablation/export/CLI and committed-example tests.

## Prompt history

| ID | Outcome | Commit |
|---|---|---|
| P0 | Scaffolding, dependencies, smoke tests done (pre-protocol) | 8c34c1d |
| P1 | PDF inspection: script, outputs, PNG, inspection.md, 11 tests pass | 0597652 |
| P2 | Image-derived GT, 43 rows; now VERIFIED by human with no corrections; 12 tests pass | 0be2cf6 (initial GT); verification: 9805d79 |
| P3 | Pure normalization utilities, 129 new tests; full suite 141 passed; GT unchanged | b41840c |
| P4 | Pure relative row/column/indent reconstruction, GT matched; 166 tests pass | 2582b5d |

## Sessions

| # | Model | UTC start | Note |
|---|---|---|---|
| 1 | Claude Opus 4.6 | unknown | P0 executed; no handoff protocol yet |
| 2 | Claude Opus 4.6 | 2026-10-22T12:54Z | P1 started; cut off by usage limit after step 1 |
| 3 | Claude Opus 4.6 | 2026-10-22T13:05Z | Ran inspect_pdf.py, generated outputs; cut off before updating workstamp |
| 4 | Claude Sonnet 4.6 | 2026-10-22T14:19Z | Resumed after interruption (usage limit) |
| 5 | GPT-6 (Codex) | 2026-10-22T18:00:38Z | Resumed in new session; previous agent hit usage limit |
