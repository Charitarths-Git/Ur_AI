"""Run deterministic RawPage geometry sweeps, ablations and parsed-value faults."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from _console import configure_utf8  # noqa: E402
from parser.evaluation.robustness import run_robustness, write_robustness  # noqa: E402


def main():
    configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "data/raw/balance_sheet_after_correction.pdf")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--gt", type=Path, default=ROOT / "data/gt/page4.csv")
    parser.add_argument("--gt-meta", type=Path, default=ROOT / "data/gt/page4_meta.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "eval/results")
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    report = run_robustness(args.pdf, args.gt, args.gt_meta, page_number=args.page,
                            seeds=args.seeds, progress=lambda text: print(text, flush=True))
    for path in write_robustness(report, args.out_dir):
        print(f"Wrote {path}")
    f = report["fault_injection"]
    print("Breakpoints:", report["breakpoints"])
    print("Fault coverage:", f["covered_cells"], "/", f["numeric_cells"])
    print("Fault detection:", f["by_fault_type"], "digit groups:", f["by_digit_group"])


if __name__ == "__main__":
    main()
