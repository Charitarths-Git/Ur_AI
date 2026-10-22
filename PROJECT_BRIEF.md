# Project Brief — Japanese Balance-Sheet PDF Parser

## Context

This is a take-home project for an internship application at **Ur AI** (Document Intelligence & VLM R&D).

## Input

A born-digital PDF of a real, publicly filed Japanese consolidated balance sheet (連結貸借対照表).

Key properties of the document:
| Property | Detail |
|---|---|
| Page | 4 of the filing |
| Label | 訂正後 ("after correction") |
| Units | 千円 (thousands of yen) |
| Columns | Previous fiscal year (前連結会計年度) and current fiscal year (当連結会計年度) |
| Negative numbers | Marked with △ (e.g. △1,234) |
| Nil values | Marked with － |
| Digits & punctuation | Mix of full-width and half-width |
| Duplicate labels | e.g. リース資産, その他, 減価償却累計額 appear under different parents |
| Hierarchy | Implied by layout (indentation, coordinates), not explicit in the text layer |
| Subtotals | May differ slightly from the sum of components due to rounding |

## Deliverables

1. **GitHub repository** with all code.
2. **Flat CSV** with columns: `label`, `parent`, `level`, `row_type`, `previous_year_value`, `current_year_value`.
3. **Hierarchical JSON** preserving section → subsection → line-item structure.
4. **Evaluation framework** covering:
   - (a) Cell-level accuracy against hand-labeled ground truth.
   - (b) Structural accuracy (hierarchy, row/column alignment).
   - (c) Label-free accounting checks (subtotals, net rows, total assets) with rounding tolerance appropriate for 千円 units.
5. **Short written report** with design decisions, results, and future work.

## Design Assumptions

- The primary input is **born-digital PDF** (has a real text layer). Build for this first.
- The code must be **structured so an OCR/VLM backend** for scanned pages can be plugged in later behind a clean interface, but that backend is **not implemented now**.
- The system must handle all quirks listed in the input properties table above.

## Planned Phases

| Phase | Scope |
|---|---|
| P0 — Setup | Repository layout, dependencies, smoke test, brief ✅ |
| P1 — Inspect the PDF | Diagnostic extraction; understand text layer, layout, coordinates |
| P2 — Ground truth | Hand-verified table from the rendered page image, independent of the parser |
| P3 — Normalization | Utilities for full-width→half-width, △, －, commas; with tests |
| P4 — Row reconstruction | Cluster words into rows, assign label vs. numeric columns |
| P5 — Hierarchy inference | Parent-path assignment from indentation + text-based rules |
| P6 — CSV and JSON export | Generate flat CSV and hierarchical JSON |
| P7 — Evaluation metrics | Cell accuracy, structural accuracy, accounting checks |
| P8 — End-to-end run | Failure analysis and robustness testing |
| P9 — Independent review | Review by a different AI agent |
| P10 — Review fixes | Apply fixes from the review |
| P11 — Write-up | Report with design decisions, results, future work |
| P12 — OCR/VLM stub | Optional backend stub for scanned pages |
| P13 — Reproducibility check | Clean-clone reproducibility verification |

## Agent Working Rules

Any agent (human or AI) working on this repository **must read `workstamp.md` before doing anything**. The workstamp file is the single source of truth for the current state of work.

**Handoff protocol summary:**
1. `workstamp.md` tracks: current prompt ID and state, the verbatim prompt text, a numbered plan with step status ([ ] / [~] / [x]), files modified, last action, decisions, issues, next action, prompt history, and session log.
2. At the start of every new prompt: read `PROJECT_BRIEF.md` and `workstamp.md`, copy the new prompt verbatim, write the plan, set state to IN PROGRESS before doing any work.
3. Mark steps [~] before starting, [x] only after verified success. Update `workstamp.md` after every step.
4. Make frequent WIP git commits. Final commit uses format `P<N>: <summary>`.
5. On session resume (IN PROGRESS state found): do NOT start over. Run `git status`, `git log -5`, `git diff`, and the test suite. Compare reality with the plan. Treat [~] as unverified. Fix inconsistencies. Add a Sessions row. Continue from the first incomplete step.

## Constraints

- Keep dependencies minimal.
- Everything must be reproducible from a fresh clone with documented commands.
- Full AI chat log must be submitted alongside the code.

