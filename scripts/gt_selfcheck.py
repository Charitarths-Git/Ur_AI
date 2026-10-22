"""Throwaway P2 schema check and informational arithmetic; not package evaluation."""

import csv
from pathlib import Path

from _console import configure_utf8

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = [
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
ROW_TYPES = {"header", "line_item", "contra", "net", "subtotal", "total"}


def path_parts(row):
    return tuple(row["parent_path"].split(" > ")) if row["parent_path"] else ()


def load_and_validate(path):
    if not path.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise ValueError("CSV must be UTF-8 with BOM")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")
        rows = list(reader)
    seen_ids, seen_paths = set(), set()
    for row in rows:
        ident = row["row_id"]
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"{ident}: malformed CSV record")
        ancestors = path_parts(row)
        if not ident or ident in seen_ids or not row["label"]:
            raise ValueError(f"{ident}: missing/duplicate ID or empty label")
        if row["row_type"] not in ROW_TYPES or int(row["level"]) != len(ancestors):
            raise ValueError(f"{ident}: row type or level inconsistent with path")
        if row["parent"] != (ancestors[-1] if ancestors else ""):
            raise ValueError(f"{ident}: immediate parent inconsistent with path")
        if ancestors and ancestors not in seen_paths:
            raise ValueError(f"{ident}: ancestor path has not appeared before this row")
        for value_col, raw_col in [
            ("previous_year_value", "prev_raw"),
            ("current_year_value", "curr_raw"),
        ]:
            value, raw = row[value_col], row[raw_col]
            if row["row_type"] == "header":
                if value or raw:
                    raise ValueError(f"{ident}: header cells must be empty")
            elif raw == "－":
                if value:
                    raise ValueError(f"{ident}: printed nil must have an empty value")
            elif not raw or not value:
                raise ValueError(f"{ident}: non-nil data cell is empty")
            else:
                int(value)
        seen_ids.add(ident)
        seen_paths.add(ancestors + (row["label"],))
    return rows


def components_for(target, rows):
    """Follow the manually recorded hierarchy; replace gross items with their net."""
    target_path = path_parts(target)
    if target["row_type"] == "net":
        gross = next(r for r in rows if path_parts(r) + (r["label"],) == target_path)
        return [gross] + [
            r for r in rows if path_parts(r) == target_path and r["row_type"] == "contra"
        ]
    components = []
    for row in rows:
        if path_parts(row) != target_path or row["row_type"] in {"subtotal", "total"}:
            continue
        child_path = target_path + (row["label"],)
        if row["row_type"] == "header":
            components.extend(
                r for r in rows if path_parts(r) == child_path and r["row_type"] == "subtotal"
            )
        elif row["row_type"] == "line_item":
            nets = [r for r in rows if path_parts(r) == child_path and r["row_type"] == "net"]
            components.extend(nets or [row])
        elif row["row_type"] == "contra":
            components.append(row)
    return components


def main():
    rows = load_and_validate(ROOT / "data/gt/page4.csv")
    print("Schema OK (including BOM, enums, paths/levels and empty nil cells).")
    print("INFORMATION ONLY: units=千円; diff=sum of present components minus printed value.")
    print("Empty nil cells stay null: omitted from known-sum and listed explicitly.")
    print("No financial pass/fail decision or tolerance is applied.")
    print("row_id | label | previous: sum / printed / diff | current: sum / printed / diff")
    for row in rows:
        if row["row_type"] not in {"subtotal", "net", "total"}:
            continue
        components = components_for(row, rows)
        results = []
        for col in ["previous_year_value", "current_year_value"]:
            known_sum = sum(int(r[col]) for r in components if r[col] != "")
            printed = int(row[col])
            results.append(f"{known_sum} / {printed} / {known_sum - printed:+d}")
        print(f"{row['row_id']} | {row['label']} | " + " | ".join(results))
        nulls = [
            f"{r['row_id']}:{col}"
            for r in components
            for col in ["previous_year_value", "current_year_value"]
            if r[col] == ""
        ]
        print(
            "  components="
            + ",".join(r["row_id"] for r in components)
            + ("; null omitted=" + ",".join(nulls) if nulls else "")
        )


if __name__ == "__main__":
    configure_utf8()
    main()
