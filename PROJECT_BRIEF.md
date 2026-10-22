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
| 0 — Setup | Repository layout, dependencies, smoke test, brief ✅ |
| 1 — Extraction | Extract raw text + coordinates from the PDF using PyMuPDF / pdfplumber |
| 2 — Parsing | Normalize text (full-width, △, －), assign hierarchy via layout rules |
| 3 — Output | Generate flat CSV and hierarchical JSON |
| 4 — Ground truth | Hand-label one page, build ground-truth CSV/JSON |
| 5 — Evaluation | Implement accuracy metrics (cell, structure, accounting checks) |
| 6 — Report | Write findings, decisions, limitations, future work |

## Constraints

- Keep dependencies minimal.
- Everything must be reproducible from a fresh clone with documented commands.
- Full AI chat log must be submitted alongside the code.
