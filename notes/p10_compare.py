"""Regenerate P8/P10/P10b comparison tables from committed experiment records."""

import json
import subprocess
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("cell_accuracy_all", "row_f1", "parent", "accounting_pass_rate", "evaluable_fraction")
# Requested quantities: cell accuracy, row F1, parent, accounting rate and coverage;
# each contains both mean and minimum, rather than dropping the worst-case result.


def coverage(statuses):
    evaluable = sum(statuses[k] for k in ("exact", "within_tolerance", "fail"))
    applicable = evaluable + statuses["not_evaluable"]
    return evaluable / applicable if applicable else None


def geometry(row, key):
    if key in row["summary"]:
        return row["summary"][key]["mean"], row["summary"][key]["worst"]
    values = [coverage(r["accounting_statuses"]) for r in row["runs"] if r["crash"] is None]
    values = [v for v in values if v is not None]
    return (mean(values), min(values)) if values else (None, None)


def fmt(value):
    return "N/A" if value is None else f"{value:.4f}"


def pair(values):
    return "/".join(fmt(v) for v in values)


def build():
    p8 = json.loads(
        (ROOT / "eval/results/baseline_P8/robustness_report.json").read_text(encoding="utf-8")
    )
    p10 = json.loads(
        subprocess.check_output(
            ["git", "show", "e40462b:eval/results/robustness_report.json"], cwd=ROOT
        )
    )
    current = json.loads((ROOT / "eval/results/robustness_report.json").read_text(encoding="utf-8"))
    lines = [
        "## P10b: measured before/after (P8 → P10 = current P10b)",
        "",
        "P8 is the preserved baseline_P8 artifact committed in86a290f before code fixes.",
        "P10 is e40462b's report (including source from5565491/7f5afbd). Current is",
        "the regenerated P10b report. Each cell below is **P8 mean/min → P10 mean/min**;",
        "P10b matches P10 on all five listed metrics at every amplitude. Coverage for",
        "P8/P10 is independently reconstructed from each run's saved status counts;",
        "their files are not rewritten. Undefined fractions/rates exclude that seed",
        "and remain N/A if none are defined. Full defined-run counts are in JSON.",
        "",
        "H is median word height. No crashes occurred in any of the360 runs in any version.",
        "",
    ]
    for axis in ("y", "x"):
        lines += [
            f"### {axis}-axis: full grid, twenty seeds each",
            "",
            "| Amplitude H | Cell mean/min | Row F1 mean/min | Parent mean/min | "
            "Accounting pass mean/min | evaluable_fraction mean/min |",
            "|---:|---|---|---|---|---|",
        ]
        for index, before in enumerate(p8["geometry"]):
            if before["axis"] != axis:
                continue
            after = p10["geometry"][index]
            now = current["geometry"][index]
            cells = []
            for key in KEYS:
                a, b, c = geometry(before, key), geometry(after, key), geometry(now, key)
                assert b == c, (axis, before["amplitude_H"], key, b, c)
                cells.append(pair(a) + " → " + pair(b))
            lines.append(f"| {before['amplitude_H']:g} | " + " | ".join(cells) + " |")
        lines += [""]
    lines += [
        "### Structural ablations: P8 → P10 → P10b",
        "",
        "Values are single deterministic runs, not averages over seeds. Accounting",
        "coverage is evaluable/applicable, computed from status counts when absent.",
        "",
        "| Mode | Cell | Row F1 | Parent | Fully correct | Accounting pass | evaluable_fraction |",
        "|---|---|---|---|---|---|---|",
    ]
    for mode in current["ablations"]:
        reports = [r["ablations"][mode]["report"] for r in (p8, p10, current)]
        cells = []
        for key in (*KEYS[:3], "fully_correct_rows", "accounting_pass_rate", "evaluable_fraction"):
            if key == "accounting_pass_rate":
                vals = [r["accounting"]["pass_rate"] for r in reports]
            elif key == "evaluable_fraction":
                vals = [coverage(r["accounting"]["statuses"]) for r in reports]
            else:
                vals = [r["metrics"][key]["score"] for r in reports]
            cells.append(" → ".join(fmt(v) for v in vals))
        lines.append("| " + mode + " | " + " | ".join(cells) + " |")
    lines += [
        "",
        "### Fault injection: P8 → P10 → P10b",
        "",
        "All versions: numeric-cell participation72/72, faults3817. Detection means",
        "a baseline-passing check becomes fail; no GT is used in this decision.",
        "",
        "| Type or digit position (units=0) | P8 detected/total | "
        "P10 detected/total | P10b detected/total |",
        "|---|---:|---:|---:|",
    ]
    for field in ("by_fault_type", "by_digit_position"):
        for key in current["fault_injection"][field]:
            cells = []
            for r in (p8, p10, current):
                v = r["fault_injection"][field][key]
                cells.append(f"{v['detected']}/{v['total']}")
            lines.append("| " + key + " | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Fault counts and detector rates are unchanged.417 numeric changes hide within",
        "tolerance;2 faults are numeric no-ops. Default tolerance remains max(1,n).",
        "The new oracle separately checks a hand-written four-addend subtotal plus",
        "gross/contra/net, enumerating its own mutations and direct residuals in the test.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    path = ROOT / "notes/failure_analysis.md"
    text = path.read_text(encoding="utf-8")
    marker = "## P10b: measured before/after"
    start_tag = "<!-- BEGIN P10B COMPARISONS -->"
    end_tag = "<!-- END P10B COMPARISONS -->"
    suffix = ""
    if start_tag in text:
        text, rest = text.split(start_tag, 1)
        _, suffix = rest.split(end_tag, 1)
    elif marker in text:
        text, rest = text.split(marker, 1)
        if "## P10b diagnosis" in rest:
            suffix = "\n\n## P10b diagnosis" + rest.split("## P10b diagnosis", 1)[1]
    elif "Historical P8 baseline" not in text:
        text = (
            "# Failure analysis — preserved P8 and current P10b evidence\n\n"
            "> Historical P8 baseline: the following original experiment table and\n"
            "> narrative describe P8. P10 changed clustering/classification/accounting;\n"
            "> current statuses and complete comparisons follow below. Original parser\n"
            "> immutability statements here apply to P7–P8 only.\n\n" + text
        )
    path.write_text(
        text.rstrip() + "\n\n" + start_tag + "\n" + build() + "\n" + end_tag + suffix,
        encoding="utf-8",
    )
