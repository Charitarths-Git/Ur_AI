"""Isolated benchmark worker; timer includes PDF open, extraction and serialization."""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--engine", choices=["parser", "pdfplumber"], required=True)
p.add_argument("--source-root", type=Path, required=True)
p.add_argument("--pdf", type=Path, required=True)
p.add_argument("--page", type=int, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--repetitions", type=int, default=5)
a = p.parse_args()
sys.path.insert(0, str(a.source_root))
from parser.export import csv_bytes, json_bytes, parse_page  # noqa: E402


def extract():
    if a.engine == "pdfplumber":
        from pdfplumber_baseline import extract as baseline

        return baseline(a.pdf, a.page)
    page = parse_page(a.pdf, a.page)
    return (
        csv_bytes(page),
        json_bytes(page),
        {
            "rows": len(page.rows),
            "warnings": [w.code for w in page.warnings],
            "status": "usable_with_warnings"
            if page.rows and page.warnings
            else "usable"
            if page.rows
            else "failed",
        },
    )


def main():
    a.out.mkdir(parents=True, exist_ok=True)
    try:
        extract()  # one excluded warmup; imports/startup excluded too
        times = []
        for _ in range(a.repetitions):
            start = time.perf_counter()
            csv_data, json_data, info = extract()
            times.append((time.perf_counter() - start) * 1000)
        (a.out / "prediction.csv").write_bytes(csv_data)
        (a.out / "prediction.json").write_bytes(json_data)
        q = statistics.quantiles(times, n=4, method="inclusive")
        info["timing_ms"] = {
            "samples": times,
            "median": statistics.median(times),
            "iqr": q[2] - q[0],
            "min": min(times),
            "max": max(times),
        }
    except Exception as exc:
        info = {
            "status": "failed",
            "error": type(exc).__name__,
            "rows": 0,
            "warnings": [],
            "timing_ms": None,
        }
    (a.out / "run.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
