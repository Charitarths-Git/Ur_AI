"""P9 independent review probes — reviewer-only throwaway script.

Probe 1: Loss row with all-negative cells and a non-listed label → classify as contra or line_item?
Probe 2: Gross item with contra child but no net child inside subtotal → accounting check outcome?
Probe 3: Label with comma, double-quote, newline through CSV export then evaluator round-trip.
Probe 4: Malformed prediction CSV (missing column) → evaluator error handling.
Probe 5: One-column page end-to-end.
Probe 6: Two total rows → balance identity check.
Probe 7: Duplicated-label case with a missing row in alignment.
Probe 8: Independent recomputation of page4 accounting figures using pdfplumber.

PYTHONIOENCODING=utf-8
"""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
from pathlib import Path

# ── repo root on path ─────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from parser.layout_types import Cell, Column, LayoutConfig, RawPage, Row
from parser.normalize import parse_amount

# ── helpers ────────────────────────────────────────────────────────────────────

def fake_word(text, x0, x1, y0=0.0, y1=10.0):
    from parser.layout_types import Word
    return Word(text=text, x0=x0, y0=y0, x1=x1, y1=y1)


def make_cell(col_idx, raw):
    return Cell(column_index=col_idx, raw=raw, amount=parse_amount(raw))


def make_row(idx, label, raws, y0=float("nan"), y1=float("nan"),
             rule=False, label_x0=10.0, indent_step=0):
    cells = tuple(make_cell(i, r) for i, r in enumerate(raws))
    return Row(
        index=idx, zone="body",
        y_top=y0, y_bottom=y1,
        label=label, label_x0=label_x0,
        indent_step=indent_step,
        cells=cells, rule_above=rule,
        source_words=(),
    )


def sep(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────
# PROBE 1 — loss row (all-negative cells, non-listed label) → row type
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 1: all-negative non-listed label")
from parser.classify import classify_row
row1 = make_row(0, "営業損失", ["△1,234", "△5,678"])
result1 = classify_row(row1)
print(f"  label='{row1.label}', row_type='{result1.row_type}', source='{result1.type_source}'")
print(f"  evidence.all_negative_cells={result1.evidence.all_negative_cells}")
# Expected: classified as 'contra' via structural fallback (all_negative_cells=True)
# This is the bug: a loss line on an income statement would be misclassified.

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 2 — gross item with contra child but NO net child → accounting check
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 2: gross+contra, no net child → accounting (subtotal should check contra is ignored?)")
from parser.evaluation.accounting import AccountRow, accounting_checks

# Tree: subtotal s1 → [gross g1, contra c1, (no net)]
# Expected: subtotal sums contribution of g1 + c1
# g1 contribution: has no net child → uses its own value
# c1 contribution: has no net child → uses its own value (printed negative)
rows_p2 = (
    AccountRow("g1", "s1", "line_item", (100,),   ("100",)),
    AccountRow("c1", "s1", "contra",    (-20,),    ("△20",)),
    AccountRow("s1", None, "subtotal",  (80,),     ("80",)),
)
checks_p2 = accounting_checks(rows_p2, ("col",))
for c in checks_p2:
    print(f"  {c.check_id}: kind={c.kind} expected={c.expected} printed={c.printed} "
          f"residual={c.residual} status={c.status}")
# With no net child, g1 contributes 100 and c1 contributes -20 → expected=80, residual=0 (exact)

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 3 — label with comma, double-quote, newline through CSV export + evaluator
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 3: special characters in label through CSV/evaluator round-trip")
from parser.evaluation.data import read_table

tricky_label = 'label,with"quote\nand newline'

# Build minimal CSV bytes manually using csv module (as export.py does)
stream = io.StringIO(newline="")
writer = csv.writer(stream, lineterminator="\n")
writer.writerow(["label", "parent", "level", "row_type",
                 "previous_year_value", "current_year_value",
                 "row_id", "parent_row_id", "parent_path",
                 "prev_raw", "curr_raw"])
writer.writerow([tricky_label, "", 0, "line_item", 1234, 5678,
                 "r1", "", "", "1,234", "5,678"])
csv_bytes = stream.getvalue().encode("utf-8-sig")

with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    f.write(csv_bytes)
    tmp_csv = Path(f.name)

try:
    table3 = read_table(tmp_csv)
    recovered_label = table3.rows[0].label
    print(f"  Written label:   {tricky_label!r}")
    print(f"  Recovered label: {recovered_label!r}")
    print(f"  Round-trip OK:   {recovered_label == tricky_label}")
finally:
    tmp_csv.unlink()

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 4 — malformed prediction CSV (missing required column) → evaluator error
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 4: missing 'row_id' column in prediction CSV")
bad_csv = "label,parent,level,row_type\n行A,,0,line_item\n".encode("utf-8-sig")

with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    f.write(bad_csv)
    tmp_bad = Path(f.name)

try:
    table4 = read_table(tmp_bad)
    print(f"  issues: {table4.issues}")
    print(f"  rows read: {len(table4.rows)}")
    # Check if evaluator gracefully surfaces missing columns
    if table4.rows:
        print(f"  first row row_id: {table4.rows[0].row_id!r}")
except Exception as e:
    print(f"  EXCEPTION: {type(e).__name__}: {e}")
finally:
    tmp_bad.unlink()

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 5 — one-column page end-to-end (pipeline does not crash)
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 5: one-column page end-to-end")
from parser.layout_types import Word
from dataclasses import replace as dc_replace

# Build a minimal RawPage with exactly one numeric column
words_p5 = [
    fake_word("資産合計", 10, 50, 20, 30),
    fake_word("1,234", 100, 130, 20, 30),
]

raw_p5 = RawPage(
    width=200, height=300,
    words=tuple(words_p5),
    rules=(),
)
from parser.rows import reconstruct_page
from parser.export import parse_layout

try:
    layout5 = reconstruct_page(raw_p5, LayoutConfig())
    body = [r for r in layout5.rows if r.zone == "body"]
    print(f"  columns detected: {len(layout5.columns)}")
    print(f"  body rows: {len(body)}")
    if layout5.columns:
        parsed5 = parse_layout(layout5, "test.pdf")
        print(f"  parsed rows: {len(parsed5.rows)}, warnings: {[w.code for w in parsed5.warnings]}")
    else:
        print("  no columns detected (header-only page)")
except Exception as e:
    print(f"  EXCEPTION: {type(e).__name__}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 6 — two total rows → balance identity check
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 6: two total rows → balance identity")
rows_p6 = (
    AccountRow("t1", None, "total", (100,), ("100",)),
    AccountRow("t2", None, "total", (100,), ("100",)),  # equal → exact
)
checks_p6 = accounting_checks(rows_p6, ("col",))
for c in checks_p6:
    print(f"  {c.check_id}: kind={c.kind} status={c.status} residual={c.residual}")

# Also test mismatch
rows_p6b = (
    AccountRow("t1", None, "total", (100,), ("100",)),
    AccountRow("t2", None, "total", (105,), ("105",)),  # differ → should fail
)
checks_p6b = accounting_checks(rows_p6b, ("col",))
for c in checks_p6b:
    print(f"  (mismatch) {c.check_id}: kind={c.kind} status={c.status} residual={c.residual}")

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 7 — duplicated label with missing row in alignment
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 7: duplicated label, one row missing in prediction")
from parser.evaluation.alignment import align_rows
from parser.evaluation.data import Table, EvalRow

def make_eval_row(row_id, label, prev, curr, parent_id=None, row_type="line_item", level=0):
    return EvalRow(
        row_id=row_id, label=label,
        parent_row_id=parent_id,
        parent="",
        parent_path="",
        level=level,
        row_type=row_type,
        values=(prev, curr),
        raws=(str(prev) if prev is not None else "", str(curr) if curr is not None else ""),
        valid=(prev is not None, curr is not None),
    )

gt_rows7 = (
    make_eval_row("g1", "その他", 100, 200),
    make_eval_row("g2", "その他", 300, 400),  # duplicate label, different values
    make_eval_row("g3", "合計",   400, 600, row_type="subtotal"),
)
pred_rows7 = (
    make_eval_row("p1", "その他", 100, 200),  # matches g1
    # g2 is missing in prediction
    make_eval_row("p2", "合計",   400, 600, row_type="subtotal"),
)
cols7 = ("previous_year", "current_year")
gt_table7   = Table(rows=gt_rows7,   columns=cols7, issues=())
pred_table7 = Table(rows=pred_rows7, columns=cols7, issues=())

aln7 = align_rows(pred_table7, gt_table7)
print(f"  pairs: {aln7.pairs}  (pred_idx, gt_idx)")
print(f"  unmatched_prediction: {aln7.unmatched_prediction}")
print(f"  unmatched_gt: {aln7.unmatched_gt}")
# Expected: (0,0) and (1,2) — second その他 left unmatched, 合計 correctly aligned

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 8 — independent recomputation using pdfplumber (accounting spot-check)
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 8: independent recomputation via pdfplumber")
PDF = REPO / "data" / "raw" / "balance_sheet_after_correction.pdf"

if not PDF.exists():
    print(f"  PDF not found at {PDF}")
else:
    try:
        import pdfplumber
        with pdfplumber.open(PDF) as doc:
            page = doc.pages[0]
            words = page.extract_words(x_tolerance=3, y_tolerance=3)

        # Filter numeric-looking words (contain digits after △ strip)
        import re
        def to_int(s):
            s2 = s.replace("△", "-").replace("▲", "-").replace(",", "").replace("，", "")
            s2 = re.sub(r"[－ー—–]", "", s2)
            try:
                return int(s2)
            except ValueError:
                return None

        nums = []
        for w in words:
            v = to_int(w["text"])
            if v is not None:
                nums.append((round(float(w["top"]), 1), round(float(w["x1"]), 1), w["text"], v))

        nums.sort()
        print(f"  Total numeric tokens extracted: {len(nums)}")
        print(f"  First 5: {nums[:5]}")
        print(f"  Last  5: {nums[-5:]}")

        # Count distinct y-groups (approximate rows)
        y_vals = sorted({y for y, _, _, _ in nums})
        y_groups = []
        for y in y_vals:
            if not y_groups or y - y_groups[-1] > 5:
                y_groups.append(y)
            else:
                y_groups[-1] = y  # update to latest in tolerance
        print(f"  Distinct row y-groups: {len(y_groups)}")
        # Expect 43 body rows; some header/footer rows will also be counted

        # Sum last column (current year) for all body rows to spot-check
        # Extract two rightmost x-columns
        x_vals = sorted({x for _, x, _, _ in nums})
        if len(x_vals) >= 2:
            right_thresh = x_vals[-1] - 5  # current year column
            current_col = [v for _, x, _, v in nums if x >= right_thresh - 5]
            print(f"  Current-col token count: {len(current_col)}")
        else:
            print(f"  Not enough x columns to extract current year column")

        # Load the committed accounting report and extract key numbers
        report_path = REPO / "eval" / "results" / "page4_report.md"
        if report_path.exists():
            text = report_path.read_text(encoding="utf-8")
            # Find total assets line
            match = re.search(r"\|[^|]*total[^|]*\|[^|]*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|", text, re.IGNORECASE)
            if match:
                print(f"  First 'total' accounting row match: {match.group(0).strip()}")
            else:
                print("  Could not find 'total' row in report (regex too strict)")
        else:
            print(f"  Accounting report not found at {report_path}")
    except ImportError:
        print("  pdfplumber not available")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PROBE 9 — brute-force fault injection on a toy tree
# ─────────────────────────────────────────────────────────────────────────────
sep("PROBE 9: brute-force fault injection on a toy tree")
from parser.evaluation.accounting import AccountRow, accounting_checks
from parser.evaluation.faults import apply_fault, iter_faults, run_fault_injection

toy_rows = (
    AccountRow("h", None, "header", (None,), ("",)),
    AccountRow("l1", "h", "line_item", (100,), ("100",)),
    AccountRow("l2", "h", "line_item", (200,), ("200",)),
    AccountRow("s1", "h", "subtotal", (300,), ("300",)),
)
toy_cols = ("value_1",)
toy_report = run_fault_injection(toy_rows, toy_cols)
toy_sub_check = next(c for c in accounting_checks(toy_rows, toy_cols) if c.row_id == "s1")
toy_faults = list(iter_faults(toy_rows))
toy_detected_brute = sum(
    next(c for c in accounting_checks(apply_fault(toy_rows, f), toy_cols) if c.row_id == "s1").status == "fail"
    for f in toy_faults
)
toy_detected_report = sum(v["detected"] for v in toy_report["by_fault_type"].values())
print(f"  Brute-force detected faults: {toy_detected_brute}/{len(toy_faults)}")
print(f"  Report detected faults:      {toy_detected_report}/{toy_report['faults']}")
print(f"  Match: {toy_detected_brute == toy_detected_report}")
print(f"  Hundreds digit detected: {toy_report['by_digit_position']['2']['detected']}/{toy_report['by_digit_position']['2']['total']}")
print(f"  Units digit detected:    {toy_report['by_digit_position']['0']['detected']}/{toy_report['by_digit_position']['0']['total']} (slips under tolerance)")

print("\n=== PROBES COMPLETE ===")
