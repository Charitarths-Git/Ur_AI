"""Print visual rows and raw geometry evidence; no file export or semantic inference."""

import argparse
import sys
from dataclasses import fields
from pathlib import Path

from _console import configure_utf8

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser.pdf_backend import read_pdf_page  # noqa: E402
from parser.rows import reconstruct_page  # noqa: E402


def main():
    configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--page", type=int, default=1, help="one-based PDF page number (default: 1)")
    args = parser.parse_args()
    layout = reconstruct_page(read_pdf_page(args.pdf_path, args.page))
    print("THRESHOLDS (input page coordinate units)")
    for field in fields(layout.thresholds):
        print(f"  {field.name}={getattr(layout.thresholds, field.name):.6f}")
    print("COLUMNS")
    for column in layout.columns:
        print(f"  {column.index}: x1={column.x1_centre:.6f} "
              f"heading={column.heading!r} period_end={column.period_end}")
    print(f"INDENT CENTRES: {layout.indent_centres}")
    print("ROWS")
    for row in layout.rows:
        cells = " ".join(f"c{c.column_index}={c.raw!r}({c.amount.status})" for c in row.cells)
        print(f"{row.index:3d} {row.zone:6s} y={row.y_top:.4f}..{row.y_bottom:.4f} "
              f"indent_step={row.indent_step} label={row.label!r} "
              f"{cells} rule_above={row.rule_above}")


if __name__ == "__main__":
    main()
