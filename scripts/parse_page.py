"""Parse one PDF page into a flat CSV and a hierarchical JSON document."""

import argparse
import sys
from collections import Counter
from pathlib import Path

from _console import configure_utf8

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser.export import parse_page, write_exports  # noqa: E402


def main():
    configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    page = parse_page(args.pdf, args.page)
    paths = write_exports(page, args.out_dir)
    print(f"Rows per type: {dict(Counter(row.row_type for row in page.rows))}")
    print(f"Hierarchy source: {page.hierarchy_source}; warnings: {len(page.warnings)}")
    for warning in page.warnings:
        print(f"  {warning.code} row={warning.row_id}: {warning.message}")
    for path in paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
