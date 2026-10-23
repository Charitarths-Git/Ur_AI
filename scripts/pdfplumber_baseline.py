"""Fixed pdfplumber text-grid baseline. No parser geometry, hierarchy or GT input."""

import csv
import io
import json

import pdfplumber

from parser.normalize import parse_amount

SETTINGS = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
    "text_x_tolerance": 3,
    "text_y_tolerance": 3,
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "intersection_tolerance": 3,
}


def extract(path, page_number):
    with pdfplumber.open(path) as pdf:
        tables = pdf.pages[page_number - 1].extract_tables(SETTINGS)
    grid = max(tables, key=len, default=[])
    records = []
    for cells in grid:
        if len(cells) < 3:
            continue
        label = "".join((c or "").replace("\n", "") for c in cells[:-2]).strip()
        raws = [(c or "").replace("\n", "").strip() for c in cells[-2:]]
        amounts = [parse_amount(s) for s in raws]
        if not label or any(a.status == "invalid" for a in amounts):
            continue
        records.append((label, raws, amounts))
    # Remove leading nonnumeric grid rows (titles and period headings), retaining
    # subsequent text-only rows. No GT-dependent cropping/role/hierarchy inference.
    first = next(
        (i for i, r in enumerate(records) if any(a.status in ("ok", "nil") for a in r[2])),
        len(records),
    )
    records = records[first:]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "label",
            "parent",
            "level",
            "row_type",
            "previous_year_value",
            "current_year_value",
            "row_id",
            "parent_row_id",
            "parent_path",
            "prev_raw",
            "curr_raw",
        ]
    )
    serialized = []
    for i, (label, raws, amounts) in enumerate(records, 1):
        writer.writerow(
            [label, "", "", "unsupported", amounts[0].value, amounts[1].value, i, "", "", *raws]
        )
        serialized.append({"label": label, "raws": raws, "values": [a.value for a in amounts]})
    return (
        stream.getvalue().encode("utf-8-sig"),
        json.dumps(serialized).encode("utf-8"),
        {
            "rows": len(records),
            "warnings": ["hierarchy_and_row_types_unsupported", "chronology_assumed_left_to_right"],
            "status": "usable_with_warnings" if records else "failed",
        },
    )
