"""Determinism, axis independence and data-derived exhaustive fault counts."""

import json
from pathlib import Path

import pytest
from test_rows import synthetic_page

from parser.evaluation.accounting import AccountRow, accounting_checks
from parser.evaluation.data import read_table
from parser.evaluation.faults import apply_fault, iter_faults, numeric_cells, run_fault_injection
from parser.evaluation.perturb import drop_rules, flatten_indentation, transform
from parser.evaluation.report import account_rows

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "mode",
    [
        "translate",
        "scale_small",
        "scale_large",
        "shuffle",
        "combined",
        "jitter",
        "jitter_x",
        "jitter_y",
    ],
)
def test_perturbations_repeat_for_same_seed(mode):
    page = synthetic_page()
    before = page.words, page.rules
    assert transform(page, mode, seed=7, amplitude=0.2) == transform(
        page, mode, seed=7, amplitude=0.2
    )
    assert (page.words, page.rules) == before


def test_axis_jitter_and_structural_helpers():
    page = synthetic_page()
    x = transform(page, "jitter_x", seed=1, amplitude=0.1)
    y = transform(page, "jitter_y", seed=1, amplitude=0.1)
    assert sorted((w.text, w.y0, w.y1) for w in x.words) == sorted(
        (w.text, w.y0, w.y1) for w in page.words
    )
    assert sorted((w.text, w.x0, w.x1) for w in y.words) == sorted(
        (w.text, w.x0, w.x1) for w in page.words
    )
    assert not drop_rules(page).rules
    assert flatten_indentation(page) == flatten_indentation(page)


def test_exhaustive_fault_population_and_detector_are_deterministic():
    table = read_table(ROOT / "examples/balance_sheet_after_correction_p1.csv")
    rows = account_rows(table)
    cells = numeric_cells(rows)
    expected_substitutions = 0
    for i, c in cells:
        digits = [char for char in rows[i].raws[c] if char.isdecimal()]
        expected_substitutions += len(digits) * 9 - int(len(digits) > 1 and int(digits[0]) != 0)
    faults = list(iter_faults(rows))
    assert faults == list(iter_faults(rows))
    assert len(faults) == expected_substitutions + 2 * len(cells)
    for fault in faults:
        if fault.kind == "digit_substitution":
            digits = [char for char in fault.raw if char.isdecimal()]
            assert len(digits) == 1 or digits[0] != "0"
    report = run_fault_injection(rows, table.columns)
    assert report == run_fault_injection(rows, table.columns)
    assert report["numeric_cells"] == len(cells)
    for kind in ["sign_flip", "blank_to_nil"]:
        assert report["by_fault_type"][kind]["total"] == len(cells)
    assert report["by_fault_type"]["digit_substitution"]["total"] == expected_substitutions
    participation = {
        cell
        for check in accounting_checks(rows, table.columns)
        if check.status in {"exact", "within_tolerance"}
        for cell in check.dependencies
    }
    assert report["covered_cells"] == sum(
        (rows[i].row_id, table.columns[c]) in participation for i, c in cells
    )


def test_committed_sweep_is_complete_and_honest_about_undefined_rates():
    report = json.loads((ROOT / "eval/results/robustness_report.json").read_text(encoding="utf-8"))
    assert report["seeds"] == list(range(20))
    assert len(report["geometry"]) == 2 * len(report["amplitudes_H"])
    assert all(len(row["runs"]) == len(report["seeds"]) for row in report["geometry"])
    assert all(
        row["crashes"] == sum(run["crash"] is not None for run in row["runs"])
        for row in report["geometry"]
    )
    for row in report["geometry"]:
        defined = sum(run["metrics"]["accounting_pass_rate"] is not None for run in row["runs"])
        assert row["summary"]["accounting_pass_rate"]["defined_runs"] == defined


def test_toy_tree_fault_injection_brute_force():
    rows = (
        AccountRow("h", None, "header", (None,), ("",)),
        AccountRow("l1", "h", "line_item", (100,), ("100",)),
        AccountRow("l2", "h", "line_item", (200,), ("200",)),
        AccountRow("s1", "h", "subtotal", (300,), ("300",)),
    )
    cols = ("value_1",)

    # 1. Baseline accounting check passes exactly
    base_checks = accounting_checks(rows, cols)
    sub_check = next(c for c in base_checks if c.row_id == "s1")
    assert sub_check.status == "exact"
    assert sub_check.expected == 300
    assert sub_check.printed == 300

    # 2. Run fault injection framework
    report = run_fault_injection(rows, cols)
    assert report["numeric_cells"] == 3
    assert report["covered_cells"] == 3

    # 3. Brute force check every generated fault independently
    faults = list(iter_faults(rows))
    detected_count = 0
    for fault in faults:
        faulty_rows = apply_fault(rows, fault)
        checks_after = {c.check_id: c for c in accounting_checks(faulty_rows, cols)}
        is_detected = checks_after[sub_check.check_id].status == "fail"
        if is_detected:
            detected_count += 1

    total_detected = sum(v["detected"] for v in report["by_fault_type"].values())
    assert total_detected == detected_count

    # Sign flips and blank to nil are 100% detected
    assert report["by_fault_type"]["sign_flip"]["detected"] == 3
    assert report["by_fault_type"]["blank_to_nil"]["detected"] == 3

    # Position 2 (hundreds digit, e.g. 100 -> 900) detected: residual 800 > tol 2
    pos2 = report["by_digit_position"]["2"]
    assert pos2["detected"] == pos2["total"]

    # Position 0 (units digit, e.g. 100 -> 101) slips under tolerance (residual 1 <= tol 2)
    pos0 = report["by_digit_position"]["0"]
    assert pos0["detected"] < pos0["total"]

