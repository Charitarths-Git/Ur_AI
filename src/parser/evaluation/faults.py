"""Exhaustive single-cell parsed-value faults; detector uses only accounting data."""

from collections import Counter
from dataclasses import dataclass, replace

from parser.evaluation.accounting import AccountRow, accounting_checks
from parser.normalize import parse_amount


@dataclass(frozen=True)
class Fault:
    row_index: int
    column_index: int
    kind: str
    digit_position: int | None
    value: int | None
    raw: str


def numeric_cells(rows):
    return tuple((i, c) for i, row in enumerate(rows) for c, value in enumerate(row.values)
                 if value is not None and parse_amount(row.raws[c]).status == "ok")


def iter_faults(rows):
    """Every decimal glyph substitution, then sign flip and nil; no random sampling.

    Position zero is the units digit. Leading-zero creation is excluded only
    for multi-digit figures. Zero sign flips are included and reported as no-ops.
    """
    for i, c in numeric_cells(rows):
        raw = rows[i].raws[c]
        digits = [pos for pos, char in enumerate(raw) if char.isdecimal()]
        for d, position in enumerate(digits):
            old = int(raw[position])
            for replacement in range(10):
                if replacement == old or (d == 0 and len(digits) > 1 and replacement == 0):
                    continue
                glyph = chr(0xFF10 + replacement) if "０" <= raw[position] <= "９" else str(replacement)
                changed = raw[:position] + glyph + raw[position + 1:]
                result = parse_amount(changed)
                yield Fault(i, c, "digit_substitution", len(digits) - d - 1, result.value, changed)
        parsed = parse_amount(raw)
        value = rows[i].values[c]
        flipped = str(-value) if value else ("0" if parsed.negative else "-0")
        yield Fault(i, c, "sign_flip", None, -value, flipped)
        yield Fault(i, c, "blank_to_nil", None, None, "－")


def apply_fault(rows, fault):
    row = rows[fault.row_index]
    values, raws = list(row.values), list(row.raws)
    values[fault.column_index], raws[fault.column_index] = fault.value, fault.raw
    result = list(rows)
    result[fault.row_index] = replace(row, values=tuple(values), raws=tuple(raws))
    return tuple(result)


def run_fault_injection(rows: tuple[AccountRow, ...], columns: tuple[str, ...]) -> dict:
    baseline = accounting_checks(rows, columns)
    passed = {c.check_id: c for c in baseline if c.status in {"exact", "within_tolerance"}}
    participation = {cell for c in passed.values() for cell in c.dependencies}
    cells = numeric_cells(rows)
    covered = [(i, c) for i, c in cells if (rows[i].row_id, columns[c]) in participation]
    kinds, positions, reasons, tolerance_sizes = {}, {}, Counter(), Counter()
    undetected = []
    total = 0
    for fault in iter_faults(rows):
        total += 1
        after = {c.check_id: c for c in accounting_checks(apply_fault(rows, fault), columns)}
        detected = any(after[ident].status == "fail" for ident in passed)
        tally = kinds.setdefault(fault.kind, Counter())
        tally["total"] += 1
        tally["detected"] += detected
        if fault.kind == "digit_substitution":
            p = positions.setdefault(fault.digit_position, Counter())
            p["total"] += 1
            p["detected"] += detected
        if detected:
            continue
        cell = (rows[fault.row_index].row_id, columns[fault.column_index])
        impacted = [after[c.check_id] for c in passed.values() if cell in c.dependencies]
        old_value = rows[fault.row_index].values[fault.column_index]
        effective_new = 0 if fault.value is None and parse_amount(fault.raw).status == "nil" else fault.value
        if not impacted:
            reason = "uncovered"
        elif old_value == effective_new:
            reason = "no_numeric_change"
        elif all(c.status in {"exact", "within_tolerance"} for c in impacted):
            reason = "within_tolerance"
            tolerance_sizes[",".join(str(n) for n in sorted({c.n for c in impacted}))] += 1
        else:
            reason = "not_evaluable_or_unchecked"
        reasons[reason] += 1
        undetected.append({"row_id": cell[0], "column": cell[1], "kind": fault.kind,
                           "digit_position": fault.digit_position, "original_value": old_value,
                           "fault_value": fault.value, "fault_raw": fault.raw, "reason": reason,
                           "checks": [{"check_id": c.check_id, "n": c.n, "residual": c.residual,
                                       "tolerance": c.tolerance, "status": c.status} for c in impacted]})
    def rate(counter):
        return {"detected": counter["detected"], "total": counter["total"],
                "rate": counter["detected"] / counter["total"] if counter["total"] else None}
    grouped = {}
    for name, pos in [("units", [0]), ("higher", [p for p in positions if p > 0])]:
        counter = Counter()
        for p in pos:
            counter.update(positions.get(p, {}))
        grouped[name] = rate(counter)
    return {"numeric_cells": len(cells), "covered_cells": len(covered),
            "coverage": len(covered) / len(cells) if cells else None,
            "uncovered_cells": [{"row_id": rows[i].row_id, "column": columns[c]}
                                for i, c in cells if (i, c) not in covered],
            "faults": total, "by_fault_type": {kind: rate(count) for kind, count in sorted(kinds.items())},
            "by_digit_position": {str(p): rate(count) for p, count in sorted(positions.items())},
            "by_digit_group": grouped, "undetected_reasons": dict(sorted(reasons.items())),
            "hidden_by_addend_counts": dict(sorted(tolerance_sizes.items())), "undetected": undetected,
            "definition": "Detected iff a baseline-passing check becomes fail. Zero/no-op faults remain in denominators."}
