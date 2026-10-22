"""Determinism, axis independence and data-derived exhaustive fault counts."""

import json
from pathlib import Path

import pytest
from test_rows import synthetic_page

from parser.evaluation.accounting import accounting_checks
from parser.evaluation.data import read_table
from parser.evaluation.faults import iter_faults, numeric_cells, run_fault_injection
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
