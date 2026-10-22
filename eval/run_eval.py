"""Score an exported prediction CSV against GT, optionally checking JSON metadata."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from _console import configure_utf8  # noqa: E402

from parser.evaluation.report import evaluate_files, write_report  # noqa: E402


def main():
    configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred", required=True, type=Path)
    parser.add_argument("--pred-json", type=Path)
    parser.add_argument("--gt", required=True, type=Path)
    parser.add_argument("--gt-meta", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "eval/results")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    report = evaluate_files(
        args.pred, args.gt, args.pred_json, args.gt_meta, threshold=args.threshold
    )
    for path in write_report(report, args.out_dir):
        print(f"Wrote {path}")
    print("GT cell accuracy:", report["metrics"]["cell_accuracy_all"])
    print("Accounting:", report["accounting"])


if __name__ == "__main__":
    main()
