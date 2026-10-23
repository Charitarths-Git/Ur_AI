"""Independent acceptance tests closing gaps in the P10 fixes (old tests retained)."""

import importlib.util
import json
from collections import Counter
from pathlib import Path
from statistics import mean

import pytest
from test_accounting import a
from test_hierarchy import layout, row
from test_rows import synthetic_page, word

from parser.evaluation.accounting import accounting_checks, accounting_summary
from parser.evaluation.faults import run_fault_injection
from parser.evaluation.perturb import transform
from parser.evaluation.report import evaluate_files, markdown_report
from parser.evaluation.robustness import robustness_markdown
from parser.export import json_document, parse_layout
from parser.layout_types import RawPage
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/balance_sheet_after_correction.pdf"


@pytest.mark.parametrize(
    "value,raw,expected",
    [(None, "－", 100), (None, "bad", None), (None, "", None), (-20, "△20", 80)],
)
def test_no_net_contra_nil_invalid_and_nested_header(value, raw, expected):
    rows = (
        a("root", None, "header", None),
        a("section", "root", "header", None),
        a("g", "section", "line_item", 100),
        a("c", "g", "contra", value, raw),
        a("s", "section", "subtotal", expected or 80),
        a("t", "root", "total", expected or 80),
    )
    checks = {c.row_id: c for c in accounting_checks(rows, ("v",)) if c.row_id}
    assert checks["s"].expected == expected
    assert checks["s"].status == ("exact" if expected is not None else "not_evaluable")
    assert ("c", "v") in checks["s"].dependencies
    # A nested header uses its printed subtotal, not a guessed re-sum of descendants.
    assert checks["t"].status == "exact"


def test_no_net_invalid_gross_cannot_be_rescued_by_contra():
    rows = (
        a("g", None, "line_item", None, "bad"),
        a("c", "g", "contra", -20),
        a("s", None, "subtotal", 80),
    )
    assert (
        next(c for c in accounting_checks(rows, ("v",)) if c.row_id == "s").status
        == "not_evaluable"
    )


def test_loss_warning_propagates_from_row_to_page_json():
    page = parse_layout(layout([row("営業損失", raws=("△10", "△20"))]), "synthetic.pdf")
    typed = page.rows[0].typed
    assert typed.row_type == "line_item"
    assert "possible_contra_or_loss" in {w.code for w in typed.warnings}
    assert "possible_contra_or_loss" in {w.code for w in page.warnings}
    assert "possible_contra_or_loss" in {w["code"] for w in json_document(page)["warnings"]}


def test_zero_evaluable_applicable_is_zero_coverage_and_na_rate(tmp_path):
    checks = accounting_checks((a("s", None, "subtotal", 1),), ("v",))
    summary = accounting_summary(checks)
    assert summary["evaluable"] == 0 and summary["applicable"] == 1
    assert summary["evaluable_fraction"] == 0 and summary["pass_rate"] is None
    path = tmp_path / "pred.csv"
    path.write_text(
        "label,parent,level,row_type,row_id,parent_row_id,parent_path,value_1,raw_1\nS,,0,subtotal,s,,,1,1\n",
        encoding="utf-8-sig",
    )
    report = evaluate_files(path, path)
    assert "Accounting pass rate=N/A; evaluable_fraction=0.000000" in markdown_report(report)
    assert report["aggregation"]["micro"]["evaluable_fraction"]["score"] == 0


def test_x_point3_seed1_has_two_columns_and_correct_roles():
    raw = read_pdf_page(PDF)
    reconstructed = reconstruct_page(transform(raw, "jitter_x", seed=1, amplitude=0.3))
    page = parse_layout(reconstructed, PDF.name)
    assert len(reconstructed.columns) == 2
    assert [c.role for c in page.columns] == ["previous_year", "current_year"]
    assert len(page.rows) == 43


def test_row_pitch_1point3_heights_with_jitter_keeps_separate_rows():
    words = []
    for i in range(10):
        y = 20 + 13 * i  # pitch 1.3 H, H=10; independently jitter label and amounts
        words += [
            word(f"Item{i}", 20, y),
            word(str(100 + i), 170, y, 30),
            word(str(200 + i), 270, y, 30),
        ]
    raw = RawPage(400, 200, words)
    for seed in range(20):
        reconstructed = reconstruct_page(transform(raw, "jitter_y", seed=seed, amplitude=0.2))
        body = [r for r in reconstructed.rows if r.zone == "body"]
        # Narrow-row gap chaining must never merge two physical row identities.
        for r in body:
            identities = [w.text for w in r.source_words if w.text.startswith("Item")]
            assert len(identities) <= 1
        assert sum(r.label.startswith("Item") for r in body) == 10


@pytest.mark.parametrize("case", ["one_column", "empty", "no_body"])
def test_degenerate_layout_warnings_reach_json(case):
    raw = (
        synthetic_page(columns=1)
        if case == "one_column"
        else RawPage(500, 600, () if case == "empty" else (word("Heading", 10, 10),))
    )
    page = parse_layout(reconstruct_page(raw), "synthetic.pdf")
    codes = {w.code for w in page.warnings}
    if case == "one_column":
        assert "one_column_detected" in codes and len(page.columns) == 1
    else:
        assert {"no_columns_detected", "no_body_rows", "empty_input"} <= codes
        assert "insufficient_indentation" not in codes
    assert codes == {w["code"] for w in json_document(page)["warnings"]}


def test_warning_visible_in_parse_cli_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("p10b_parse_cli", ROOT / "scripts/parse_page.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    page = parse_layout(reconstruct_page(synthetic_page(columns=1)), "synthetic.pdf")
    monkeypatch.setattr(cli, "parse_page", lambda *args: page)
    monkeypatch.setattr("sys.argv", ["parse_page.py", "synthetic.pdf", "--out-dir", str(tmp_path)])
    cli.main()
    assert "one_column_detected" in capsys.readouterr().out


def test_committed_robustness_coverage_mean_min_and_markdown():
    report = json.loads((ROOT / "eval/results/robustness_report.json").read_text(encoding="utf-8"))
    for group in report["geometry"]:
        fractions = [
            r["metrics"]["evaluable_fraction"]
            for r in group["runs"]
            if r["metrics"]["evaluable_fraction"] is not None
        ]
        summary = group["summary"]["evaluable_fraction"]
        assert summary["mean"] == (mean(fractions) if fractions else None)
        assert summary["worst"] == (min(fractions) if fractions else None)
        for run in group["runs"]:
            if run["crash"] is None:
                statuses = run["accounting_statuses"]
                evaluable = sum(statuses[k] for k in ("exact", "within_tolerance", "fail"))
                applicable = evaluable + statuses["not_evaluable"]
                assert run["metrics"]["evaluable_fraction"] == (
                    evaluable / applicable if applicable else None
                )
    text = robustness_markdown(report)
    assert "pass rate | evaluable_fraction" in text
    assert "mean / minimum" in text
    assert text == (ROOT / "eval/results/robustness_report.md").read_text(encoding="utf-8")


def test_independent_fault_oracle_four_addends_and_net():
    # All generation and check arithmetic below are independent of library fault/check code.
    # Contributions: net(120-20)=100, then 80, 50,40; subtotal=270.
    specs = [
        ("gross", "h", "line_item", 120),
        ("contra", "gross", "contra", -20),
        ("net", "gross", "net", 100),
        ("b", "h", "line_item", 80),
        ("c", "h", "line_item", 50),
        ("d", "h", "line_item", 40),
        ("sum", "h", "subtotal", 270),
    ]
    rows = (a("h", None, "header", None),) + tuple(a(*s) for s in specs)
    values = {s[0]: s[3] for s in specs}

    def fails(v):
        return (
            abs(v["net"] - v["gross"] - v["contra"]) > 2
            or abs(v["sum"] - v["net"] - v["b"] - v["c"] - v["d"]) > 4
        )

    assert not fails(values)
    totals, detected, positions, position_detected = Counter(), Counter(), Counter(), Counter()
    for ident, value in values.items():
        digits = str(abs(value))
        mutations = [("sign_flip", None, -value), ("blank_to_nil", None, 0)]
        for index, original in enumerate(digits):
            for digit in "0123456789":
                if digit == original or (index == 0 and len(digits) > 1 and digit == "0"):
                    continue
                number = int(digits[:index] + digit + digits[index + 1 :]) * (
                    -1 if value < 0 else 1
                )
                mutations.append(("digit_substitution", str(len(digits) - index - 1), number))
        for kind, position, number in mutations:
            changed = dict(values, **{ident: number})
            is_detected = fails(changed)
            totals[kind] += 1
            detected[kind] += is_detected
            if position is not None:
                positions[position] += 1
                position_detected[position] += is_detected
    report = run_fault_injection(rows, ("value_1",))
    for kind in totals:
        assert report["by_fault_type"][kind]["total"] == totals[kind]
        assert report["by_fault_type"][kind]["detected"] == detected[kind]
    for position in positions:
        assert report["by_digit_position"][position]["total"] == positions[position]
        assert report["by_digit_position"][position]["detected"] == position_detected[position]
