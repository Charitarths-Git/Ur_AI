"""P2: schema only; no financial values or row-count expectations."""

import csv
from pathlib import Path


def test_gt_schema():
    path = Path(__file__).resolve().parents[1] / "data/gt/page4.csv"
    columns = {
        "row_id", "label", "parent", "parent_path", "level", "row_type",
        "previous_year_value", "current_year_value", "prev_raw", "curr_raw",
    }
    allowed = {"header", "line_item", "contra", "net", "subtotal", "total"}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        assert columns.issubset(reader.fieldnames or [])
        for row in reader:
            assert row["row_type"] in allowed
            ancestors = row["parent_path"].split(" > ") if row["parent_path"] else []
            assert int(row["level"]) == len(ancestors)
