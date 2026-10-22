# workstamp.md

## Status

| Field | Value |
|---|---|
| Prompt | P5-P6 |
| State | IN PROGRESS |
| GT | VERIFIED by human; read-only |
| Updated | 2026-10-22T22:51:02Z |

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
7. [x] Add synthetic, real GT, byte-invariance, ablation/export/CLI/example tests; commit section 7.
8. [x] Document patterns, evidence counts, ablation, schemas and limitations; commit section 8.
9. [~] Full suite then ruff; integrity checks; final commit and DONE handoff.

## Files created or modified

- notes/inspection.md — Q5 five-step/root correction, separate fix commit.
- src/parser/rules.py — immutable replaceable RuleSet and Japanese default.
- src/parser/classify.py — ordered row types, independent evidence and typed warnings.
- src/parser/hierarchy.py — explicit parent-stack tree and partial flat fallback.
- src/parser/metadata.py — unit-line cleanup, header/footer metadata and date-based roles.
- src/parser/export.py — frozen ParsedPage, pure assembly/serializers and I/O wrappers.
- scripts/parse_page.py — UTF-8 CLI writing both deliverables and summary.
- examples/balance_sheet_after_correction_p1.csv and .json — real-page generated outputs.
- .gitattributes — LF for example bytes across operating systems.
- tests/test_hierarchy.py, test_metadata.py, test_export.py — synthetic and end-to-end coverage.
- notes/hierarchy_and_export.md — algorithms, RuleSet validation status, evidence and ablation.
- README.md — pipeline, CLI, APIs, schemas, examples and P7-P8 next phase.
- workstamp.md — verbatim prompt, section-by-section progress and evidence.

## Last action and result

Orientation: clean at 9012bae; baseline 166 passed in 6.73s. Existing Session 5.
Final full suite: 223 passed in 7.88s (57 new tests). Ruff package/scripts/new tests:
All checks passed! No assertions weakened. Pytest temporary-dir setup needed
unsandboxed execution; the unchanged rerun succeeded. git diff --check passes.

GT: exact label, parent, parent_row_id, parent_path, level, row_type, both values
and both raw fields each match 43/43. Metadata unit/correction/printed page/dates
match; hierarchy_source=indentation, real warning list empty. Four ruled headers
are accepted. Report includes independent evidence counts and pattern validity.
Six transformations give byte-identical CSV and JSON; committed examples equal
fresh in-memory and CLI generation. CLI passes with encoding env removed.

Flat-indentation ablation: fallback with warning; types/values unchanged;
38/43 parent IDs agree (diagnostic only, no score asserted). Wrong: allowance
contra row, three subsection headers, fixed-assets subtotal. A provisional
39/43 handoff note was corrected to measured 38/43 before completion.

All GT/raw hashes unchanged, including CSV
c26ba476e9537c7f1748cef09109b810ca1356f80f96acb5955761ad17174835.
P3/P4 production code and dependency manifests unchanged. Verbatim prompt exact.

Commits: d28504f Q5 fix; e00ca2f unit-heading fix; 93ecd54 RuleSet; 712c2b1 types;
4cb6d06 hierarchy; eeded2a metadata; d466446 export/CLI/examples;
8cc4dbf tests; 7f9eb82 docs/report/style. Final P5-P6 commit next.

## Decisions and assumptions

- Frozen RuleSet owns all language-specific patterns; matches use label_key and
  printed output labels are unchanged. Only supplied printed page 4 has real-document
  validation; liability/equity/self-stock/other-unit patterns are untested heuristics.
- Classification order is structural no-cells, total, net, subtotal, contra, then
  all-negative fallback. Numeric sign evidence excludes nil/invalid cells; negative
  zero counts negative. Contra warning requires no negative numeric cell at all.
- Strictly smaller indent stack gives parents; levels count ancestors. Insufficient
  indentation always warns and uses the deliberately partial rule fallback.
- P4 raw headings remain unchanged; metadata removes whole unit lines. Titles are
  remaining header text, dates/known markers excluded. Missing metadata stays None.
- Two distinct dates set chronological roles; all other cases use generic roles with
  warning. Values remain printed units; unit multiplier is metadata only.
- ParsedPage is frozen; pure stages and byte serializers sit between explicit PDF
  backend and output writers. IDs are one-based body order; tree is an ordered forest.
- CSV BOM/LF and JSON Unicode/indent=2/LF are deterministic. Source stores basename,
  one-based PDF page/backend only; no timestamps/absolute paths/geometry in exports.
- .gitattributes enforces LF only for generated examples; GT attributes untouched.
- No evaluation metrics module or OCR/VLM implementation. No P7/P8 work started.

## Known issues / open questions

No unresolved failures or open questions. Known limitations are documented in
notes/hierarchy_and_export.md: flat hierarchy, unknown header nesting, missing
subtotal keywords, label-less rows, page-spanning/multiple tables, non-Japanese
rules and scanned pages, plus inherited P4 geometry limits. Fallback can attach
contra/net across older contexts, changing tree traversal vs flat order. The
configured upstream origin/main is gone; no remote work requested.

## Next action

Create final P5-P6 commit, then record its hash and DONE status for P7-P8 evaluation framework.

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
