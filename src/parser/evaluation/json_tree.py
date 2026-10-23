"""Validate untrusted JSON trees separately from CSV, deriving actual ancestry."""

from parser.evaluation.data import EvalRow, Table, value_at
from parser.evaluation.metrics import ratio, score_tables
from parser.normalize import parse_amount


def validate_tree(document, csv_table, truth, *, threshold=0.5):
    errors, rows, seen = [], [], set()

    def error(path, code):
        errors.append({"path": path, "code": code})

    if not isinstance(document, dict):
        document = {}
        error("$", "expected_object")
    if document.get("schema_version") != "1.0":
        error("$.schema_version", "unsupported_schema")
    for name in ("source", "page"):
        if not isinstance(document.get(name), dict):
            error("$." + name, "expected_object")
    if not isinstance(document.get("warnings"), list):
        error("$.warnings", "expected_array")
    if not isinstance(document.get("hierarchy_source"), str):
        error("$.hierarchy_source", "expected_string")
    columns = document.get("columns")
    roles, indices = [], []
    if not isinstance(columns, list) or not columns:
        error("$.columns", "expected_nonempty_array")
        columns = []
    for i, col in enumerate(columns):
        path = f"$.columns[{i}]"
        if not isinstance(col, dict):
            error(path, "expected_object")
            continue
        role, index = col.get("role"), col.get("index")
        if not isinstance(role, str) or not role or role in roles:
            error(path + ".role", "missing_or_duplicate_role")
            continue
        if type(index) is not int or index < 0 or index in indices:
            error(path + ".index", "invalid_or_duplicate_index")
        if not isinstance(col.get("heading"), str):
            error(path + ".heading", "expected_string")
        if col.get("period_end") is not None and not isinstance(col["period_end"], str):
            error(path + ".period_end", "expected_string_or_null")
        roles.append(role)
        indices.append(index)

    def visit(nodes, parent=None, labels=(), path="$.rows"):
        if not isinstance(nodes, list):
            error(path, "expected_array")
            return
        for i, node in enumerate(nodes):
            loc = f"{path}[{i}]"
            if not isinstance(node, dict):
                error(loc, "expected_object")
                continue
            ident = node.get("row_id")
            if type(ident) is int:
                ident = str(ident)
            if not isinstance(ident, str) or not ident or ident in seen:
                error(loc + ".row_id", "missing_or_duplicate_id")
                ident = "__invalid_node__:" + loc
            seen.add(ident)
            label, kind = node.get("label"), node.get("row_type")
            if not isinstance(label, str) or not label:
                error(loc + ".label", "expected_nonempty_string")
                label = ""
            if kind not in ("header", "line_item", "subtotal", "total", "contra", "net"):
                error(loc + ".row_type", "invalid_row_type")
                kind = "__invalid__"
            if type(node.get("level")) is not int or node["level"] != len(labels):
                error(loc + ".level", "declared_level_differs_from_nesting")
            if "parent_row_id" in node and node["parent_row_id"] != parent:
                error(loc + ".parent_row_id", "declared_parent_differs_from_nesting")
            values = node.get("values")
            if not isinstance(values, dict):
                error(loc + ".values", "expected_object")
                values = {}
            if set(values) != set(roles):
                error(loc + ".values", "value_roles_differ_from_columns")
            amounts, raws, valid = [], [], []
            for role in roles:
                record = values.get(role)
                ok = isinstance(record, dict)
                record = record if ok else {}
                raw, amount, status = record.get("raw"), record.get("value"), record.get("status")
                ok &= isinstance(raw, str) and (amount is None or type(amount) is int)
                parsed = parse_amount(raw) if isinstance(raw, str) else None
                ok &= (
                    parsed is not None
                    and parsed.status == status
                    and parsed.value == amount
                    and status in ("ok", "nil", "empty")
                )
                if not ok:
                    error(loc + ".values." + role, "invalid_value_record")
                amounts.append(amount if type(amount) is int else None)
                raws.append(raw if isinstance(raw, str) else "")
                valid.append(bool(ok))
            rows.append(
                EvalRow(
                    ident,
                    label,
                    parent,
                    labels[-1] if labels else "",
                    " > ".join(labels),
                    len(labels),
                    kind,
                    tuple(amounts),
                    tuple(raws),
                    tuple(valid),
                )
            )
            if len(labels) >= 128:
                error(loc, "maximum_tree_depth_exceeded")
            else:
                visit(node.get("children"), ident, labels + (label,), loc + ".children")

    visit(document.get("rows"))
    if not rows:
        error("$.rows", "empty_tree")
    table = Table(tuple(rows), tuple(roles))
    by_id = {row.row_id: row for row in rows}
    csv_ids = {row.row_id: row for row in csv_table.rows}
    differences, correct = [], 0
    for ident in sorted(set(by_id) | set(csv_ids)):
        a, b = by_id.get(ident), csv_ids.get(ident)
        fields = []
        if a is None or b is None:
            fields = ["missing_json_node" if a is None else "extra_json_node"]
        else:
            for field in ("label", "parent_row_id", "parent_path", "level", "row_type"):
                if getattr(a, field) != getattr(b, field):
                    fields.append(field)
            for role in sorted(set(table.columns) | set(csv_table.columns)):
                if value_at(table, a, role) != value_at(csv_table, b, role):
                    fields.append("values." + role)
        if fields:
            differences.append({"row_id": ident, "fields": fields})
        else:
            correct += 1
    scored = score_tables(table, truth, threshold=threshold)
    return {
        "status": "invalid" if errors else "valid",
        "errors": errors,
        "derived_rows": len(rows),
        "csv_consistency": {
            "consistent": not errors and not differences,
            "rows": ratio(
                correct,
                len(set(by_id) | set(csv_ids)),
                "identical rows by ID / union of CSV and JSON IDs",
            ),
            "differences": differences,
        },
        "gt_accuracy": scored,
        "passes": not errors and not differences and not scored["mismatches"],
    }
