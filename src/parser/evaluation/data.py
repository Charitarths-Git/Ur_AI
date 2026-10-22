"""Independent exported-file records; no internal parsed-page objects are consumed."""

import csv
from dataclasses import dataclass, replace
from pathlib import Path

from parser.normalize import parse_amount


@dataclass(frozen=True)
class EvalRow:
    row_id: str
    label: str
    parent_row_id: str | None
    parent: str
    parent_path: str
    level: int | None
    row_type: str
    values: tuple[int | None, ...]
    raws: tuple[str, ...]
    valid: tuple[bool, ...]


@dataclass(frozen=True)
class Table:
    rows: tuple[EvalRow, ...]
    columns: tuple[str, ...]
    issues: tuple[str, ...] = ()


def read_table(path: str | Path, *, ground_truth: bool = False) -> Table:
    """Read P6 or GT UTF-8-BOM CSV. GT missing parent IDs are derived from paths.

    Numeric values come from value fields, never reparsed from raw as a correction.
    Raw parse validity distinguishes invalid missing amounts from legitimate nulls.
    Unknown prediction roles remain unknown; they are not remapped using GT values.
    """
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        required = {"row_id", "label", "parent", "parent_path", "level", "row_type"}
        if not required <= set(fields):
            raise ValueError(f"missing CSV fields: {sorted(required - set(fields))}")
        value_fields = [f for f in fields if f.endswith("_value") or f.startswith("value_")]
        columns = tuple(f.removesuffix("_value") for f in value_fields)
        raw_fields = [
            "prev_raw"
            if c == "previous_year"
            else "curr_raw"
            if c == "current_year"
            else f"raw_{i + 1}"
            for i, c in enumerate(columns)
        ]
        if not set(raw_fields) <= set(fields):
            raise ValueError("missing raw value columns")
        records = list(reader)
    rows, issues, seen = [], [], set()
    paths = {}
    for index, record in enumerate(records, 1):
        ident = record["row_id"]
        if not ident or ident in seen:
            raise ValueError("row IDs must be nonempty and unique")
        seen.add(ident)
        parent_id = record.get("parent_row_id") or None
        ancestors = tuple(record["parent_path"].split(" > ")) if record["parent_path"] else ()
        if ground_truth and "parent_row_id" not in fields:
            parent_id = paths.get(ancestors)
            if ancestors and parent_id is None:
                raise ValueError(f"GT parent path not found before row {ident}")
        paths[ancestors + (record["label"],)] = ident
        values, raws, valid = [], [], []
        for value_field, raw_field in zip(value_fields, raw_fields, strict=True):
            text, raw = record[value_field], record[raw_field]
            try:
                value = int(text) if text else None
                is_valid = value is not None or parse_amount(raw).status in {"nil", "empty"}
            except ValueError:
                value, is_valid = None, False
                issues.append(f"row {ident}: invalid integer in {value_field}")
            values.append(value)
            raws.append(raw)
            valid.append(is_valid)
        try:
            level = int(record["level"])
        except ValueError:
            level = None
            issues.append(f"row {ident}: invalid level")
        rows.append(
            EvalRow(
                ident,
                record["label"],
                parent_id,
                record["parent"],
                record["parent_path"],
                level,
                record["row_type"],
                tuple(values),
                tuple(raws),
                tuple(valid),
            )
        )
    if not ground_truth and "parent_row_id" not in fields:
        issues.append("prediction lacks parent_row_id; nonroot parent links cannot be credited")
        rows = [
            replace(r, parent_row_id="__missing_parent__") if r.parent_path else r for r in rows
        ]
    return Table(tuple(rows), columns, tuple(issues))


def value_at(table: Table, row: EvalRow, role: str):
    if role not in table.columns:
        return None, "", False
    index = table.columns.index(role)
    return row.values[index], row.raws[index], row.valid[index]
