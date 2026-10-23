"""Reproduce fixed-split benchmark; source downloads are explicit and never part of CI."""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from pdfplumber_baseline import SETTINGS  # noqa: E402

from parser.evaluation.data import Table, read_table  # noqa: E402
from parser.evaluation.metrics import aggregate_reports, score_tables  # noqa: E402
from parser.normalize import parse_amount  # noqa: E402

STRUCTURAL = {
    "row_type",
    "level",
    "parent",
    "parent_path",
    "ancestor_jaccard",
    "fully_correct_rows",
}


def truth_csv(ident, destination):
    annotation = json.loads((ROOT / "benchmarks/annotations" / f"{ident}.json").read_text("utf-8"))
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        [
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
    )
    stack = []
    for i, row in enumerate(annotation["rows"], 1):
        depth = row["depth"]
        stack = stack[:depth]
        if len(stack) != depth:
            raise ValueError("annotation depth skips a parent")
        amounts = [parse_amount(raw).value for raw in row["raws"]]
        writer.writerow(
            [
                str(i),
                row["label"],
                stack[-1] if stack else "",
                " > ".join(stack),
                depth,
                row["row_type"],
                *amounts,
                *row["raws"],
            ]
        )
        stack.append(row["label"])
    destination.write_bytes(out.getvalue().encode("utf-8-sig"))


def frozen_source(commit, folder):
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "src/parser"], cwd=ROOT, text=True
    ).splitlines()
    for name in names:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT))
    return folder / "src"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--download", action="store_true")
    p.add_argument("--render", action="store_true", help="render annotation review images")
    p.add_argument("--cache", type=Path, default=ROOT / "outputs/benchmark_sources")
    p.add_argument("--out-dir", type=Path, default=ROOT / "eval/results/benchmark")
    p.add_argument("--repetitions", type=int, default=5)
    args = p.parse_args()
    if args.repetitions < 2:
        p.error("at least two repetitions are required")
    manifest = json.loads((ROOT / "benchmarks/manifest.json").read_text("utf-8"))
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        name: frozen_source(manifest[field], ROOT / "outputs/frozen" / name)
        for name, field in [("original", "baseline_commit"), ("candidate", "candidate_commit")]
    }
    sources["pdfplumber"] = sources["candidate"]
    reports = []
    for doc in manifest["documents"]:
        pdf = args.cache / (doc["id"] + ".pdf")
        if args.download and not pdf.exists():
            try:
                data = urllib.request.urlopen(
                    doc["url"], timeout=60, context=ssl.create_default_context()
                ).read()
                pdf.write_bytes(data)
            except Exception as exc:
                print(doc["id"], "download failed:", type(exc).__name__)
        if not pdf.exists() or hashlib.sha256(pdf.read_bytes()).hexdigest() != doc["sha256"]:
            raise SystemExit(f"{doc['id']}: missing or changed PDF; see manifest URL and SHA256")
        if args.render:
            import pymupdf

            with pymupdf.open(pdf) as opened:
                opened[doc["page"] - 1].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(
                    str(args.cache / (doc["id"] + ".png"))
                )
        truth_path = ROOT / "outputs" / (doc["id"] + "_truth.csv")
        truth_csv(doc["id"], truth_path)
        gt = read_table(truth_path, ground_truth=True)
        for engine, source in sources.items():
            dest = ROOT / "outputs/benchmark_runs" / doc["id"] / engine
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/benchmark_worker.py"),
                    "--engine",
                    "pdfplumber" if engine == "pdfplumber" else "parser",
                    "--source-root",
                    str(source),
                    "--pdf",
                    str(pdf),
                    "--page",
                    str(doc["page"]),
                    "--out",
                    str(dest),
                    "--repetitions",
                    str(args.repetitions),
                ],
                check=True,
                cwd=ROOT,
            )
            run = json.loads((dest / "run.json").read_text("utf-8"))
            pred = (
                read_table(dest / "prediction.csv")
                if run["status"] != "failed"
                else Table((), gt.columns)
            )
            scores = score_tables(pred, gt)
            if engine == "pdfplumber":
                for key in STRUCTURAL:
                    scores["metrics"][key] = {
                        "numerator": 0,
                        "denominator": 0,
                        "score": None,
                        "meaning": "unsupported by this baseline; N/A",
                    }
            result = {
                "document": doc["id"],
                "split": doc["split"],
                "engine": engine,
                "annotation_status": "AI_DRAFT",
                "run": run,
                **scores,
            }
            reports.append(result)
            print(
                doc["id"],
                engine,
                run["status"],
                scores["metrics"]["cell_accuracy_all"]["numerator"],
                "/",
                len(gt.rows) * 2,
                flush=True,
            )
    aggregate = {}
    for split in ["development", "held_out"]:
        aggregate[split] = {}
        for engine in sources:
            subset = [r for r in reports if r["split"] == split and r["engine"] == engine]
            aggregate[split][engine] = aggregate_reports(subset)
    result = {
        "manifest": manifest,
        "pdfplumber_settings": SETTINGS,
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "processor": platform.processor(),
            "packages": {
                k: importlib.metadata.version(k) for k in ["PyMuPDF", "pdfplumber", "pdfminer.six"]
            },
        },
        "timing_policy": {
            "warmup": 1,
            "repetitions": args.repetitions,
            "boundary": "PDF open/read, extraction, normalization and in-memory output serialization; excludes process/import startup, output writes, annotations and evaluation. OS file cache warm; no cache flush.",
            "variability": "inclusive quartile IQR in milliseconds",
        },
        "pages": reports,
        "aggregation": aggregate,
    }
    (args.out_dir / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Provisional additional-page benchmark",
        "",
        "AI-drafted image annotations; NOT independently checked or human verified. "
        "Five issuers in one industry; four similarly styled templates. No broad generalisation claim.",
        "",
        "| Page | Split | Engine | Cells | Labels (normalized) | Parents | Full rows | Missing/extra | Median / IQR ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def count(metric):
        return f"{metric['numerator']}/{metric['denominator']}" if metric["denominator"] else "N/A"

    for r in reports:
        met = r["metrics"]
        t = r["run"]["timing_ms"]
        lines.append(
            "| "
            + " | ".join(
                [
                    r["document"],
                    r["split"],
                    r["engine"],
                    count(met["cell_accuracy_all"]),
                    count(met["label_key"]),
                    count(met["parent"]),
                    count(met["fully_correct_rows"]),
                    f"{len(r['alignment']['unmatched_gt'])}/{len(r['alignment']['unmatched_prediction'])}",
                    f"{t['median']:.2f} / {t['iqr']:.2f}" if t else "failed",
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Pooled counts and per-page means",
        "",
        "| Split | Engine | Pooled cells | Mean page cell score | Pooled parents | Mean page parent score |",
        "|---|---|---|---|---|---|",
    ]
    for split, engines in aggregate.items():
        for engine, a in engines.items():
            lines.append(
                f"| {split} | {engine} | {count(a['micro']['cell_accuracy_all'])} | "
                f"{a['macro']['cell_accuracy_all']['score']} | {count(a['micro']['parent'])} | "
                f"{a['macro']['parent']['score']} |"
            )
    lines += ["", "## Failures and warnings (all selected pages retained)", ""]
    for r in reports:
        lines.append(
            f"- {r['document']} / {r['engine']}: {r['run']['status']}; "
            f"warnings={r['run']['warnings']}; mismatches={len(r['mismatches'])}."
        )
    lines += [
        "",
        "Full per-page counts, raw/printed-cell metrics, every mismatch, "
        "pooled and per-page-average denominators, package/hardware details and individual "
        "timings are in report.json. Baseline structural metrics are N/A, not correct. "
        "All issuers use million-yen units. An asset-only page is not a complete statement.",
        "",
        "Reproduce: python scripts/run_benchmark.py --download --render",
        "",
    ]
    (args.out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
