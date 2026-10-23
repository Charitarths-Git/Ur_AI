"""File-scored robustness experiments; raw PDF is read once, never modified."""

import json
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory

from parser.evaluation.data import read_table
from parser.evaluation.faults import run_fault_injection
from parser.evaluation.perturb import drop_rules, flatten_indentation, transform
from parser.evaluation.report import account_rows, evaluate_files
from parser.export import csv_bytes, json_bytes, parse_layout
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

AMPLITUDES = (0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0)
GT_METRICS = ("cell_accuracy_all", "row_f1", "parent")
PRIMARY = (*GT_METRICS, "accounting_pass_rate", "evaluable_fraction")


def run_robustness(
    pdf_path,
    gt_path,
    gt_meta_path=None,
    *,
    page_number=1,
    seeds=20,
    amplitudes=AMPLITUDES,
    progress=None,
):
    if seeds < 1:
        raise ValueError("seeds must be positive")
    raw = read_pdf_page(pdf_path, page_number)
    h = reconstruct_page(raw).thresholds
    result = {
        "schema_version": "1.0",
        "source": Path(pdf_path).name,
        "seeds": list(range(seeds)),
        "amplitudes_H": list(amplitudes),
        "median_word_height": h.median_word_height,
        "thresholds_H": {
            "row_tolerance": h.row_tolerance / h.median_word_height,
            "column_tolerance": h.column_tolerance / h.median_word_height,
            "indent_tolerance": h.indent_tolerance / h.median_word_height,
        },
        "geometry": [],
        "ablations": {},
    }
    with TemporaryDirectory(prefix="balance-evaluation-") as temporary:
        pred_csv, pred_json = (
            Path(temporary) / "prediction.csv",
            Path(temporary) / "prediction.json",
        )

        def score(page):
            parsed = parse_layout(reconstruct_page(page), Path(pdf_path).name, page_number)
            pred_csv.write_bytes(csv_bytes(parsed))
            pred_json.write_bytes(json_bytes(parsed))
            report = evaluate_files(
                pred_csv, gt_path, pred_json if gt_meta_path else None, gt_meta_path
            )
            return parsed, report

        base, baseline = score(raw)
        result["baseline"] = baseline
        # Restore this file before fault injection, which reads prediction only.
        prediction = read_table(pred_csv)
        result["fault_injection"] = run_fault_injection(
            account_rows(prediction), prediction.columns
        )
        for axis in ("y", "x"):
            for amplitude in amplitudes:
                runs = []
                for seed in range(seeds):
                    try:
                        parsed, report = score(transform(raw, f"jitter_{axis}", seed, amplitude))
                        metrics = {key: report["metrics"][key]["score"] for key in GT_METRICS}
                        metrics["accounting_pass_rate"] = report["accounting"]["pass_rate"]
                        metrics["evaluable_fraction"] = report["accounting"]["evaluable_fraction"]
                        runs.append(
                            {
                                "seed": seed,
                                "crash": None,
                                "metrics": metrics,
                                "hierarchy_source": parsed.hierarchy_source,
                                "warnings": [w.code for w in parsed.warnings],
                                "rows": len(parsed.rows),
                                "mismatches": len(report["mismatches"]),
                                "mismatch_examples": report["mismatches"][:12],
                                "accounting_statuses": report["accounting"]["statuses"],
                            }
                        )
                    except Exception as error:
                        # Existing parser failures are recorded, not repaired in this phase.
                        runs.append(
                            {
                                "seed": seed,
                                "crash": f"{type(error).__name__}: {error}",
                                "metrics": {
                                    key: 0.0 if key in GT_METRICS else None for key in PRIMARY
                                },
                            }
                        )
                summary = {}
                for key in PRIMARY:
                    values = [
                        run["metrics"][key] for run in runs if run["metrics"][key] is not None
                    ]
                    summary[key] = {
                        "mean": mean(values) if values else None,
                        "worst": min(values) if values else None,
                        "defined_runs": len(values),
                        "attempted_runs": seeds,
                    }
                row = {
                    "axis": axis,
                    "amplitude_H": amplitude,
                    "summary": summary,
                    "crashes": sum(run["crash"] is not None for run in runs),
                    "runs": runs,
                }
                result["geometry"].append(row)
                if progress:
                    progress(
                        f"{axis} jitter {amplitude:g} H: cell "
                        f"mean={summary['cell_accuracy_all']['mean']:.4f}, "
                        f"worst={summary['cell_accuracy_all']['worst']:.4f}, "
                        f"crashes={row['crashes']}"
                    )
        modes = {
            "flatten_indentation": flatten_indentation(raw),
            "drop_rules": drop_rules(raw),
            **{
                mode: transform(raw, mode)
                for mode in ["translate", "scale_small", "scale_large", "shuffle"]
            },
        }
        for mode, page in modes.items():
            try:
                parsed, report = score(page)
                result["ablations"][mode] = {
                    "crash": None,
                    "hierarchy_source": parsed.hierarchy_source,
                    "parser_warnings": [w.code for w in parsed.warnings],
                    "report": report,
                }
            except Exception as error:
                result["ablations"][mode] = {"crash": f"{type(error).__name__}: {error}"}
        result["breakpoints"] = {
            axis: next(
                (
                    r["amplitude_H"]
                    for r in result["geometry"]
                    if r["axis"] == axis
                    and (r["crashes"] or any(r["summary"][key]["worst"] != 1 for key in GT_METRICS))
                ),
                None,
            )
            for axis in ["y", "x"]
        }
    result["limitations"] = [
        "Single development page, not a generalisation claim.",
        "Uniform per-word translation jitter, not OCR image noise; rules remain unjittered.",
        "Crash runs count as zero for GT sweep scores; undefined accounting rates are "
        "excluded with defined_runs reported.",
        "First degraded tested amplitude is not a universal geometric bound.",
        "Existing parser bugs are documented, not fixed here.",
    ]
    return result


def robustness_markdown(report):
    def pct(value):
        return f"{value:.4f}" if value is not None else "N/A"

    lines = [
        "# Robustness experiments — one development page",
        "",
        f"Seeds: {report['seeds']}. Jitter units: median word height.",
        "",
        f"Baseline accounting pass rate={pct(report['baseline']['accounting']['pass_rate'])}; "
        f"evaluable_fraction={pct(report['baseline']['accounting']['evaluable_fraction'])}.",
        "",
        "## Geometry sweep",
        "",
        "Each entry is mean / minimum over defined seeds. "
        "See JSON for all seed records and defined-run counts.",
        "",
        "| Axis | H amplitude | Cell accuracy | Row F1 | Parent accuracy | Accounting "
        "pass rate | evaluable_fraction | Crashes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["geometry"]:
        scores = [
            pct(row["summary"][key]["mean"]) + " / " + pct(row["summary"][key]["worst"])
            for key in PRIMARY
        ]
        lines.append(
            f"| {row['axis']} | {row['amplitude_H']} | "
            + " | ".join(scores)
            + f" | {row['crashes']} |"
        )
    lines += [
        "",
        f"First degraded tested amplitude: {report['breakpoints']}.",
        "",
        "## Structural ablations",
        "",
        "The JSON includes the full metric set and accounting checks for each.",
        "",
        "| Mode | Cell accuracy | Row F1 | Parent | Full rows | Accounting pass rate | "
        "evaluable_fraction | Parser warnings |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, ablation in report["ablations"].items():
        if ablation["crash"]:
            lines.append(f"| {mode} | CRASH | | | | | | |")
            continue
        r = ablation["report"]
        metrics = [
            pct(r["metrics"][key]["score"])
            for key in ["cell_accuracy_all", "row_f1", "parent", "fully_correct_rows"]
        ]
        lines.append(
            f"| {mode} | " + " | ".join(metrics) + f" | {pct(r['accounting']['pass_rate'])} "
            f"| {pct(r['accounting']['evaluable_fraction'])} "
            f"| {len(ablation['parser_warnings'])} |"
        )
    f = report["fault_injection"]
    lines += [
        "",
        "## Exhaustive parsed-value fault injection",
        "",
        f"Coverage: {f['covered_cells']}/{f['numeric_cells']}; generated faults: {f['faults']}.",
        "",
        "| Fault | Detected | Total | Rate |",
        "|---|---:|---:|---:|",
    ]
    for name, value in f["by_fault_type"].items():
        lines.append(f"| {name} | {value['detected']} | {value['total']} | {pct(value['rate'])} |")
    lines += ["", "| Digit position from units | Detected | Total | Rate |", "|---|---:|---:|---:|"]
    for pos, value in f["by_digit_position"].items():
        lines.append(f"| {pos} | {value['detected']} | {value['total']} | {pct(value['rate'])} |")
    lines += [
        "",
        f"Units vs higher digits: {f['by_digit_group']}.",
        f"Undetected reasons: {f['undetected_reasons']}.",
        f"Within-tolerance faults grouped by impacted addend counts: "
        f"{f['hidden_by_addend_counts']}.",
        "",
        "Every undetected fault and its impacted n/residual/tolerance are listed in JSON.",
        "A last-digit error can hide inside a many-addend sum's tolerance. "
        "Printed-zero sign flips and blanking zero do not change arithmetic.",
        "",
        "## Limitations",
        "",
        *(f"- {s}" for s in report["limitations"]),
    ]
    return "\n".join(lines) + "\n"


def write_robustness(report, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    j, m = out / "robustness_report.json", out / "robustness_report.md"
    j.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    m.write_bytes(robustness_markdown(report).encode("utf-8"))
    return j, m
