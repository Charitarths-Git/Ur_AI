"""Label-free accounting: IDs, parent IDs, types and amount/raw tuples only.

No GT, label text, language rules or hierarchy inference enters this module.
Residual is printed minus expected. Truncation bounds are diagnostic, not gates.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from parser.normalize import parse_amount


@dataclass(frozen=True)
class AccountRow:
    row_id: str
    parent_row_id: str | None
    row_type: str
    values: tuple[int | None, ...]
    raws: tuple[str, ...]


class ToleranceModel(Protocol):
    def __call__(self, n: int) -> int: ...


def addend_tolerance(n: int) -> int:
    return max(1, n)


@dataclass(frozen=True)
class AccountingCheck:
    check_id: str
    kind: str
    row_id: str | None
    value_column: str
    n: int
    expected: int | None
    printed: int | None
    residual: int | None
    tolerance: int | None
    status: str
    truncation_lower: int | None
    truncation_upper: int | None
    truncation_consistent: bool | None
    dependencies: tuple[tuple[str, str], ...]


def _number(row, col):
    value = row.values[col]
    if value is not None:
        return value
    return 0 if parse_amount(row.raws[col]).status == "nil" else None


def accounting_checks(
    rows: tuple[AccountRow, ...],
    columns: tuple[str, ...],
    tolerance_model: ToleranceModel = addend_tolerance,
) -> tuple[AccountingCheck, ...]:
    """Rebuild sibling groups in file order; never inspect labels or compare to GT.

    A net child replaces gross contribution. Otherwise use own amount, or a lone
    subtotal child's amount for a header. Ambiguous/missing components are NE.
    """
    rows = tuple(rows)
    by_id = {r.row_id: r for r in rows}
    children = {}
    for row in rows:
        children.setdefault(row.parent_row_id, []).append(row)

    def contribution(row, col):
        nets = [r for r in children.get(row.row_id, []) if r.row_type == "net"]
        if nets:
            return (_number(nets[0], col), nets[0].row_id) if len(nets) == 1 else (None, row.row_id)
        if row.values[col] is not None or row.raws[col] or row.row_type != "header":
            return _number(row, col), row.row_id
        totals = [r for r in children.get(row.row_id, []) if r.row_type == "subtotal"]
        return (
            (_number(totals[0], col), totals[0].row_id) if len(totals) == 1 else (None, row.row_id)
        )

    results = []

    def emit(kind, row, col, parts, applicable=True):
        role = columns[col]
        ident = row.row_id if row else None
        n = len(parts)
        values = [value for value, _ in parts]
        expected = sum(values) if values and all(v is not None for v in values) else None
        printed = _number(row, col) if row else None
        tolerance = tolerance_model(n) if applicable else None
        if tolerance is not None and tolerance < 0:
            raise ValueError("tolerance must be nonnegative")
        residual = printed - expected if printed is not None and expected is not None else None
        if not applicable:
            status = "not_applicable"
        elif residual is None:
            status = "not_evaluable"
        else:
            status = (
                "exact"
                if residual == 0
                else "within_tolerance"
                if abs(residual) <= tolerance
                else "fail"
            )
        low = -sum(v < 0 for v in values) if residual is not None else None
        high = sum(v > 0 for v in values) - 1 if residual is not None else None
        consistent = low <= residual <= high if residual is not None else None
        dependencies = tuple(
            dict.fromkeys([(rid, role) for _, rid in parts] + ([(ident, role)] if ident else []))
        )
        results.append(
            AccountingCheck(
                f"{kind}:{ident or 'page'}:{role}",
                kind,
                ident,
                role,
                n,
                expected,
                printed,
                residual,
                tolerance,
                status,
                low,
                high,
                consistent,
                dependencies,
            )
        )

    for row in rows:
        if row.row_type in {"subtotal", "total"}:
            siblings = children.get(row.parent_row_id, [])
            preceding = siblings[: siblings.index(row)]
            for col in range(len(columns)):
                parts = [contribution(sibling, col) for sibling in preceding]
                if row.parent_row_id is not None and row.parent_row_id not in by_id:
                    parts = [(None, row.parent_row_id)]
                emit(row.row_type, row, col, parts)
        elif row.row_type == "net":
            parent = by_id.get(row.parent_row_id)
            contras = [r for r in children.get(row.parent_row_id, []) if r.row_type == "contra"]
            for col in range(len(columns)):
                parts = [(_number(parent, col), parent.row_id)] if parent else []
                parts += [(_number(c, col), c.row_id) for c in contras]
                if parent is None or not contras:
                    parts.append((None, row.row_id))
                emit("net", row, col, parts)
    totals = [row for row in rows if row.row_type == "total"]
    for col in range(len(columns)):
        if len(totals) == 2:
            emit("balance", totals[1], col, [(_number(totals[0], col), totals[0].row_id)])
        else:
            emit("balance", None, col, [], applicable=False)
    return tuple(results)


def accounting_summary(checks: tuple[AccountingCheck, ...]) -> dict:
    counts = Counter(c.status for c in checks)
    evaluable = sum(counts[s] for s in ["exact", "within_tolerance", "fail"])
    passed = counts["exact"] + counts["within_tolerance"]
    diagnostic = [c for c in checks if c.truncation_consistent is not None]
    inside = sum(c.truncation_consistent for c in diagnostic)
    return {
        "statuses": {
            s: counts[s]
            for s in ["exact", "within_tolerance", "fail", "not_evaluable", "not_applicable"]
        },
        "passed": passed,
        "evaluable": evaluable,
        "pass_rate": passed / evaluable if evaluable else None,
        "truncation_inside": inside,
        "truncation_evaluable": len(diagnostic),
        "truncation_fraction": inside / len(diagnostic) if diagnostic else None,
        "truncation_note": "Hypothesis diagnostic only; never affects status/pass rate.",
    }
