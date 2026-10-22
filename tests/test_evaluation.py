"""Independent scoring semantics: alignment, denominators, identity and file CLI."""

import csv
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from parser.evaluation.alignment import align_rows
from parser.evaluation.data import EvalRow, Table, read_table
from parser.evaluation.metrics import aggregate_reports, score_tables
from parser.evaluation.report import evaluate_files, markdown_report

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "examples/balance_sheet_after_correction_p1.csv"
PJSON = PRED.with_suffix(".json")
GT = ROOT / "data/gt/page4.csv"
META = ROOT / "data/gt/page4_meta.json"
COLS = ("previous_year", "current_year")


def erow(ident, label, values=(12, 34), parent=None, path="", level=0, kind="line_item", raws=None):
    return EvalRow(
        ident,
        label,
        parent,
        "",
        path,
        level,
        kind,
        values,
        raws if raws is not None else tuple(str(v) if v is not None else "" for v in values),
        tuple(True for _ in values),
    )


def table(*rows):
    return Table(tuple(rows), COLS)


def score(pred, gt):
    return score_tables(pred, gt)["metrics"]


def test_perfect_prediction_and_aggregation():
    t = table(erow("1", "A"))
    result = score_tables(t, t)
    assert all(m["score"] == 1 for m in result["metrics"].values() if m["denominator"])
    twice = aggregate_reports([result, result])
    for key, metric in result["metrics"].items():
        assert twice["micro"][key]["numerator"] == metric["numerator"] * 2
        assert twice["micro"][key]["denominator"] == metric["denominator"] * 2
        assert twice["micro"][key]["score"] == metric["score"]
        assert twice["macro"][key]["score"] == metric["score"]


@pytest.mark.parametrize("changed,expected", [((13, 34), 0.5), ((34, 12), 0), ((None, 34), 0.5)])
def test_wrong_cell_swapped_columns_and_missing_amount(changed, expected):
    gt = table(erow("g", "A"))
    pred = table(erow("p", "A", changed))
    m = score(pred, gt)
    assert m["cell_accuracy_all"]["score"] == expected
    assert m["cell_accuracy_printed"]["score"] == expected
    assert m["fully_correct_rows"]["score"] == 0
    assert m["row_f1"]["score"] == 1  # an aligned row need not have correct cells


def test_none_and_zero_are_distinct_and_raws_are_separate():
    gt = table(erow("g", "A", (None, 0), raws=("－", "△0")))
    pred = table(erow("p", "A", (0, 0), raws=("0", "0")))
    m = score(pred, gt)
    assert m["cell_accuracy_all"]["score"] == 0.5
    assert m["raw_accuracy"]["score"] == 0
    assert m["cell_accuracy_printed"]["denominator"] == 2


def test_missing_row_counts_even_empty_header_cells_wrong():
    gt = table(erow("h", "Root", (None, None), kind="header"), erow("g", "A"))
    pred = table(erow("p", "A"))
    m = score(pred, gt)
    assert m["cell_accuracy_all"]["numerator"] == 2
    assert m["cell_accuracy_all"]["denominator"] == 4
    assert m["cell_accuracy_printed"]["score"] == 1
    assert m["row_recall"]["score"] == 0.5
    assert m["row_f1"]["score"] == pytest.approx(2 / 3)


def test_extra_row_reduces_precision():
    gt = table(erow("g", "A"))
    pred = table(erow("p", "A"), erow("extra", "ZZZZ", (98, 99)))
    result = score_tables(pred, gt)
    assert result["metrics"]["row_precision"]["score"] == 0.5
    assert result["metrics"]["row_recall"]["score"] == 1
    assert result["mismatches"][-1]["field"] == "extra_row"


@pytest.mark.parametrize("extra", [False, True])
def test_duplicate_labels_with_missing_or_extra_value_distinguishes_rows(extra):
    gt = table(*(erow(f"g{i}", "その他", (i, i + 10)) for i in range(3)))
    if extra:
        pred = table(
            replace(gt.rows[0], row_id="p0"),
            erow("x", "その他", (99, 98)),
            replace(gt.rows[1], row_id="p1"),
            replace(gt.rows[2], row_id="p2"),
        )
        assert align_rows(pred, gt).pairs == ((0, 0), (2, 1), (3, 2))
    else:
        pred = table(replace(gt.rows[0], row_id="p0"), replace(gt.rows[2], row_id="p2"))
        assert align_rows(pred, gt).pairs == ((0, 0), (1, 2))


def test_identical_tie_chooses_earliest_pair():
    pred = table(erow("p", "Same"))
    gt = table(erow("g1", "Same"), erow("g2", "Same"))
    assert align_rows(pred, gt).pairs == ((0, 0),)
    with pytest.raises(ValueError):
        align_rows(pred, gt, threshold=1.1)


def test_wrong_parent_not_credited_for_matching_duplicate_parent_labels():
    gt = table(
        erow("g0", "Root", (None, None), kind="header"),
        erow("g1", "Group", (None, None), "g0", "Root", 1, "header"),
        erow("g2", "Leaf", (1, 2), "g1", "Root > Group", 2),
        erow("g3", "Group", (None, None), "g0", "Root", 1, "header"),
        erow("g4", "Leaf", (3, 4), "g3", "Root > Group", 2),
    )
    mapping = {r.row_id: f"p{i}" for i, r in enumerate(gt.rows)}
    pred_rows = [
        replace(r, row_id=mapping[r.row_id], parent_row_id=mapping.get(r.parent_row_id))
        for r in gt.rows
    ]
    pred_rows[2] = replace(pred_rows[2], parent_row_id="p3")
    m = score(table(*pred_rows), gt)
    assert m["parent"]["score"] == 4 / 5
    assert m["parent_path"]["score"] == 1  # labels alone conceal the wrong parent ID
    assert m["ancestor_jaccard"]["score"] < 1


def test_unaligned_parent_is_wrong_and_does_not_map_to_root():
    gt = table(erow("g", "Leaf"))
    pred = table(
        erow("extra", "ZZZZ", (98, 99)), erow("p", "Leaf", parent="extra", path="ZZZZ", level=1)
    )
    m = score(pred, gt)
    assert m["parent"]["score"] == 0
    assert m["ancestor_jaccard"]["score"] == 0


def test_wrong_type_level_and_label_typo():
    gt = table(erow("g", "Cash"))
    pred = table(erow("p", "Cosh", kind="subtotal", level=2))
    r = score_tables(pred, gt)
    assert r["metrics"]["row_f1"]["score"] == 1
    for field in ["label_exact", "label_key", "row_type", "level"]:
        assert r["metrics"][field]["score"] == 0
    assert r["metrics"]["cell_accuracy_all"]["score"] == 1
    assert r["confusion_matrix"] == {"line_item": {"subtotal": 1}}


def test_label_key_and_raw_accuracy_do_not_replace_exact_metrics():
    gt = table(erow("g", "Other（純額）", (1000, 2), raws=("1,000", "2")))
    pred = table(erow("p", "Other (純額)", (1000, 2), raws=("1000", "2")))
    m = score(pred, gt)
    assert m["label_key"]["score"] == 1 and m["label_exact"]["score"] == 0
    assert m["raw_accuracy"]["score"] == 0.5 and m["cell_accuracy_all"]["score"] == 1


@pytest.mark.parametrize("empty_pred,empty_gt", [(True, False), (False, True), (True, True)])
def test_empty_inputs_and_undefined_denominators(empty_pred, empty_gt):
    p = table() if empty_pred else table(erow("p", "A"))
    g = table() if empty_gt else table(erow("g", "A"))
    r = score_tables(p, g)
    assert r["metrics"]["cell_accuracy_all"]["score"] == (None if empty_gt else 0)
    assert r["metrics"]["row_f1"]["score"] == (None if empty_pred and empty_gt else 0)


def test_column_role_and_period_assignment_independently():
    t = table(erow("1", "A"))
    meta = {"period_end_dates": {"previous": "(2025年3月31日)", "current": "(2026年3月31日)"}}
    columns = [
        {"index": 0, "role": "previous_year", "period_end": "2025-03-31"},
        {"index": 1, "role": "current_year", "period_end": "2026-03-31"},
    ]
    r = score_tables(t, t, predicted_json={"columns": columns}, gt_meta=meta)
    assert r["metrics"]["column_roles"]["score"] == r["metrics"]["column_periods"]["score"] == 1
    swapped = [dict(c, role=columns[1 - i]["role"]) for i, c in enumerate(columns)]
    r = score_tables(t, t, predicted_json={"columns": swapped}, gt_meta=meta)
    assert r["metrics"]["column_roles"]["score"] == 0
    assert r["metrics"]["column_periods"]["score"] == 1


def test_real_page_all_applicable_scores_are_perfect():
    r = evaluate_files(PRED, GT, PJSON, META)
    assert all(m["score"] == 1 for m in r["metrics"].values())
    assert not r["mismatches"]
    assert all(
        c["status"] in {"exact", "within_tolerance"}
        for c in r["accounting_checks"]
        if c["kind"] != "balance"
    )
    assert r["accounting"]["pass_rate"] == 1
    print("Accounting statuses/truncation:", r["accounting"])
    assert "NOT a generalisation claim" in markdown_report(r)
    pooled = aggregate_reports([r, r])
    assert (
        pooled["micro"]["accounting_pass_rate"]["denominator"] == 2 * r["accounting"]["evaluable"]
    )
    assert (
        pooled["micro"]["accounting_pass_rate"]["score"]
        == pooled["macro"]["accounting_pass_rate"]["score"]
        == 1
    )


def test_missing_roles_cannot_credit_empty_cells_and_have_reasons():
    gt = table(erow("g", "Header", (None, None), kind="header"))
    pred = Table(gt.rows, ("value_1", "value_2"))
    r = score_tables(pred, gt)
    assert r["metrics"]["cell_accuracy_all"]["score"] == 0
    assert any(
        m.get("reason") == "missing role or invalid prediction value" for m in r["mismatches"]
    )


def test_file_reader_gt_paths_and_invalid_cells(tmp_path):
    fields = [
        "row_id",
        "label",
        "parent",
        "parent_path",
        "level",
        "row_type",
        "previous_year_value",
        "current_year_value",
        "prev_raw",
        "curr_raw",
    ]
    path = tmp_path / "truth.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow(dict(zip(fields, ["r1", "Root", "", "", "0", "header", "", "", "", ""])))
        writer.writerow(
            dict(
                zip(
                    fields,
                    ["r2", "Child", "Root", "Root", "1", "line_item", "abc", "", "bad", "－"],
                )
            )
        )
    t = read_table(path, ground_truth=True)
    assert t.rows[1].parent_row_id == "r1"
    assert t.rows[1].valid == (False, True)
    assert t.issues


def test_cli_without_encoding_environment_and_committed_report(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8=0",
            str(ROOT / "eval/run_eval.py"),
            "--pred",
            str(PRED),
            "--pred-json",
            str(PJSON),
            "--gt",
            str(GT),
            "--gt-meta",
            str(META),
            "--out-dir",
            str(tmp_path),
        ],
        env=env,
        cwd=ROOT,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    data = json.loads((tmp_path / "page4_report.json").read_text(encoding="utf-8"))
    assert data == evaluate_files(PRED, GT, PJSON, META)
    assert data == json.loads((ROOT / "eval/results/page4_report.json").read_text(encoding="utf-8"))
