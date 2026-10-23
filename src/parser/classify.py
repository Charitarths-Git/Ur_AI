"""Pure row classification with independent structural evidence and typed warnings."""

from dataclasses import dataclass
from typing import Literal

from parser.layout_types import PageLayout, ParseWarning, Row
from parser.rules import JA_FINANCIAL_STATEMENT, RuleSet

RowType = Literal["header", "line_item", "contra", "net", "subtotal", "total"]


@dataclass(frozen=True)
class StructuralEvidence:
    rule_above: bool
    all_negative_cells: bool
    no_cells: bool
    has_negative_cells: bool


@dataclass(frozen=True)
class TypedRow:
    row: Row
    row_type: RowType
    type_source: Literal["label_rule", "structural"]
    evidence: StructuralEvidence
    warnings: tuple[ParseWarning, ...]


def classify_row(
    row: Row, rules: RuleSet = JA_FINANCIAL_STATEMENT, row_id: int | None = None
) -> TypedRow:
    numeric = [c for c in row.cells if c.amount.status == "ok"]
    evidence = StructuralEvidence(
        row.rule_above,
        bool(numeric) and all(c.amount.negative for c in numeric),
        not row.cells,
        any(c.amount.negative for c in numeric),
    )
    source = "label_rule"
    if evidence.no_cells:
        kind, source = "header", "structural"
    elif rules.exact(row.label, rules.total_labels) or rules.suffix(
        row.label, rules.total_suffixes
    ):
        kind = "total"
    elif rules.suffix(row.label, rules.net_suffixes):
        kind = "net"
    elif rules.suffix(row.label, rules.subtotal_suffixes):
        kind = "subtotal"
    elif rules.prefix(row.label, rules.contra_labels):
        kind = "contra"
    else:
        # Note on loss rows: rows with all-negative cells without an explicit contra prefix
        # (e.g. operating losses 営業損失) are classified as line_item, not contra,
        # with a possible_contra_or_loss warning emitted.
        kind, source = "line_item", "structural"
    warnings = []
    if kind in {"subtotal", "net", "total"} and not evidence.rule_above:
        warnings.append(
            ParseWarning("missing_rule_above", f"{kind} label has no rule above", row_id)
        )
    if kind == "contra" and not evidence.has_negative_cells:
        warnings.append(
            ParseWarning(
                "contra_without_negative", "contra label has no negative numeric cell", row_id
            )
        )
    if evidence.all_negative_cells and not rules.prefix(row.label, rules.contra_labels):
        warnings.append(
            ParseWarning(
                "possible_contra_or_loss",
                "all-negative numeric cells without contra label prefix",
                row_id,
            )
        )
    if row.cells and not row.label:
        warnings.append(
            ParseWarning("unlabeled_value_row", "value row has no printed label", row_id)
        )
    return TypedRow(row, kind, source, evidence, tuple(warnings))


def classify_rows(
    layout: PageLayout, rules: RuleSet = JA_FINANCIAL_STATEMENT
) -> tuple[TypedRow, ...]:
    return tuple(
        classify_row(row, rules, index)
        for index, row in enumerate((r for r in layout.rows if r.zone == "body"), 1)
    )
