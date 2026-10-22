"""Public file evaluator and deterministic human/machine-readable reports."""

import json
from dataclasses import asdict
from pathlib import Path

from parser.evaluation.accounting import AccountRow, accounting_checks, accounting_summary
from parser.evaluation.data import read_table
from parser.evaluation.metrics import aggregate_reports, score_tables

LIMITATIONS = (
    "Single page only; micro and macro averages coincide for this one page.",
    "Parser rules were designed after seeing this page: development results, NOT a generalisation claim.",
    "GT was drafted by an AI agent and verified by one human; the user also reported an independent second review.",
    "The truncation hypothesis rests on one page and must be verified by the human; it does not set pass/fail.",
    "Alignment can be ambiguous for identical repeated labels/values; earliest-pair ties do not prove identity.",
    "Accounting tests consistency of predicted structure, not truth; absent or wrong checks can escape detection.",
)


def account_rows(table):
    return tuple(AccountRow(r.row_id, r.parent_row_id, r.row_type, r.values, r.raws) for r in table.rows)


def evaluate_files(pred_csv, gt_csv, pred_json=None, gt_meta=None, *, threshold=0.5) -> dict:
    prediction, truth = read_table(pred_csv), read_table(gt_csv, ground_truth=True)
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else None
    report = score_tables(prediction, truth, threshold=threshold,
                          predicted_json=load(pred_json), gt_meta=load(gt_meta))
    checks = accounting_checks(account_rows(prediction), prediction.columns)
    report.update({"schema_version": "1.0", "inputs": {"prediction": Path(pred_csv).name,
                   "gt": Path(gt_csv).name}, "accounting": accounting_summary(checks),
                   "accounting_checks": [asdict(c) for c in checks], "limitations": list(LIMITATIONS)})
    report["aggregation"] = aggregate_reports([report])
    return report


def _display(value):
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_report(report: dict) -> str:
    lines = ["# Development evaluation: supplied page 4", "", "## Metrics and denominators", "",
             "| Metric | Correct / denominator | Score | Meaning |", "|---|---:|---:|---|"]
    for name, m in report["metrics"].items():
        score = f'{m["score"]:.6f}' if m["score"] is not None else "N/A"
        lines.append(f'| {name} | {m["numerator"]} / {m["denominator"]} | {score} | {m["meaning"]} |')
    lines += ["", "Undefined denominators are N/A, not perfect scores. Missing GT rows count as wrong.",
              "", "## Alignment", "", f'Matched {report["alignment"]["matched"]} rows; '
              f'prediction={report["alignment"]["predicted_rows"]}, GT={report["alignment"]["gt_rows"]}. '
              f'Threshold={report["alignment"]["threshold"]}.', "", "## Type confusion matrix", ""]
    matrix = report["confusion_matrix"]
    columns = sorted({c for row in matrix.values() for c in row})
    lines += ["| GT \\ predicted | " + " | ".join(columns) + " |", "|---|" + "---:|" * len(columns)]
    for kind, row in matrix.items():
        lines.append(f"| {kind} | " + " | ".join(str(row.get(c, 0)) for c in columns) + " |")
    lines += ["", "## Every mismatch", ""]
    if not report["mismatches"]:
        lines.append("None.")
    else:
        lines += ["| GT row | Prediction row | Label | Field | Expected | Predicted |", "|---|---|---|---|---|---|"]
        for item in report["mismatches"]:
            lines.append("| " + " | ".join(_display(item[k]) for k in
                         ["gt_row_id", "pred_row_id", "label", "field", "expected", "predicted"]) + " |")
    if report["input_issues"]:
        lines += ["", "Input issues:", "", *(f"- {s}" for s in report["input_issues"])]
    lines += ["", "## Label-free accounting", "",
              "Residual = printed minus expected; tolerance = max(1, number of addends).",
              "Nil raw marks alone allow a null to contribute zero; invalid/empty amounts are not evaluable.",
              "", "| Kind | Row | Column | n | Expected | Printed | Residual | Tolerance | Status | Truncation interval | Inside |",
              "|---|---|---|---:|---:|---:|---:|---:|---|---|---|"]
    for check in report["accounting_checks"]:
        interval = f'[{check["truncation_lower"]},{check["truncation_upper"]}]' if check["residual"] is not None else "N/A"
        cells = [check[k] for k in ["kind", "row_id", "value_column", "n", "expected", "printed",
                                    "residual", "tolerance", "status"]]
        cells += [interval, check["truncation_consistent"]]
        lines.append("| " + " | ".join(_display(c) for c in cells) + " |")
    summary = report["accounting"]
    lines += ["", f'Accounting passes: {summary["passed"]}/{summary["evaluable"]}; statuses={summary["statuses"]}.',
              f'Truncation interval consistency: {summary["truncation_inside"]}/{summary["truncation_evaluable"]}. '
              "This is a hypothesis diagnostic, never a pass/fail criterion.",
              "", "## Limitations of this evaluation", "", *(f"- {s}" for s in report["limitations"])]
    return "\n".join(lines) + "\n"


def write_report(report, out_dir):
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    j, m = directory / "page4_report.json", directory / "page4_report.md"
    j.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    m.write_bytes(markdown_report(report).encode("utf-8"))
    return j, m
