"""Synthetic-only RuleSet, classification and parent-stack tests."""

from dataclasses import FrozenInstanceError

import pytest

from parser.classify import classify_row, classify_rows
from parser.hierarchy import build_hierarchy
from parser.layout_types import Cell, Column, RawPage, Row
from parser.normalize import parse_amount
from parser.rows import reconstruct_page
from parser.rules import JA_FINANCIAL_STATEMENT, RuleSet


def row(label, step=0, raws=(), rule=False, index=0, zone="body"):
    cells = tuple(Cell(i, raw, parse_amount(raw)) for i, raw in enumerate(raws))
    return Row(
        index,
        zone,
        index * 20,
        index * 20 + 10,
        label,
        step * 10 if step is not None else None,
        step,
        cells,
        rule,
        (),
    )


def layout(rows=(), columns=None):
    empty = reconstruct_page(RawPage(500, 600))
    if columns is None:
        columns = (
            Column(0, 200, "Earlier\n(2025年3月31日)", (2025, 3, 31)),
            Column(1, 300, "Later\n(2026年3月31日)", (2026, 3, 31)),
        )
    return type(empty)(tuple(rows), tuple(columns), (), empty.thresholds)


@pytest.mark.parametrize(
    "label,raws,kind,source",
    [
        ("資産合計", (), "header", "structural"),
        ("資産合計", ("10",), "total", "label_rule"),
        ("負債純資産合計", ("10",), "total", "label_rule"),
        ("負債及び純資産合計", ("10",), "total", "label_rule"),
        ("負債・純資産合計", ("10",), "total", "label_rule"),
        ("Group合計", ("10",), "subtotal", "label_rule"),
        ("Item （純額）", ("10",), "net", "label_rule"),
        ("Item(純額)", ("10",), "net", "label_rule"),
        ("減価償却累計額", ("△10",), "contra", "label_rule"),
        ("貸倒引当金追加", ("△0",), "contra", "label_rule"),
        ("自己株式", ("△10",), "contra", "label_rule"),
        ("Unknown", ("△10", "△0"), "line_item", "structural"),
        ("Unknown", ("△10", "－"), "line_item", "structural"),
        ("営業損失", ("△1234", "△5678"), "line_item", "structural"),
        ("Unknown", ("△10", "20"), "line_item", "structural"),
        ("Unknown", ("－",), "line_item", "structural"),
        ("Unknown", ("1.5",), "line_item", "structural"),
        ("", ("10",), "line_item", "structural"),
    ],
)
def test_classification_order_and_structural_fallback(label, raws, kind, source):
    typed = classify_row(row(label, raws=raws, rule=True))
    assert (typed.row_type, typed.type_source) == (kind, source)
    assert typed.evidence.no_cells is (not raws)
    assert typed.evidence.rule_above


@pytest.mark.parametrize(
    "label,raws,rule,code",
    [
        ("資産合計", ("1",), False, "missing_rule_above"),
        ("Item合計", ("1",), False, "missing_rule_above"),
        ("Item（純額）", ("1",), False, "missing_rule_above"),
        ("貸倒引当金", ("1",), True, "contra_without_negative"),
        ("", ("1",), False, "unlabeled_value_row"),
    ],
)
def test_evidence_conflicts_are_warnings_not_overrides(label, raws, rule, code):
    typed = classify_row(row(label, raws=raws, rule=rule), row_id=7)
    assert code in {w.code for w in typed.warnings}
    assert all(w.row_id == 7 for w in typed.warnings)
    assert typed.evidence.all_negative_cells is False
    if label:
        assert typed.type_source == "label_rule"


def test_ruled_header_and_negative_zero_contra_do_not_warn():
    assert not classify_row(row("Heading", rule=True)).warnings
    typed = classify_row(row("貸倒引当金", raws=("△0",)))
    assert typed.evidence.all_negative_cells and not typed.warnings


def test_loss_row_warns_possible_contra_or_loss():
    typed = classify_row(row("営業損失", raws=("△1234", "△5678"), rule=False), row_id=12)
    assert typed.row_type == "line_item"
    assert typed.type_source == "structural"
    assert "possible_contra_or_loss" in {w.code for w in typed.warnings}
    assert any(w.row_id == 12 for w in typed.warnings)


def test_rules_can_be_replaced_and_are_frozen():
    rules = RuleSet(
        total_labels=("ALL",),
        subtotal_suffixes=("SUB",),
        net_suffixes=("NET",),
        contra_labels=("REDUCE",),
        unit_multipliers={"units": 1},
    )
    assert classify_row(row("ALL", raws=("10",)), rules).row_type == "total"
    assert classify_row(row("資産合計", raws=("10",)), rules).row_type == "line_item"
    with pytest.raises(FrozenInstanceError):
        rules.total_labels = ()
    with pytest.raises(TypeError):
        rules.unit_multipliers["units"] = 2
    assert JA_FINANCIAL_STATEMENT.exact("資 産 合 計", JA_FINANCIAL_STATEMENT.total_labels)


def test_stack_parents_paths_siblings_and_section_subtotal():
    rows = [
        row("Root", 0),
        row("A", 1),
        row("Other", 2, ("10",)),
        row("減価償却累計額", 3, ("△1",)),
        row("Other（純額）", 3, ("9",), True),
        row("A合計", 2, ("9",), True),
        row("B", 1),
        row("Other", 2, ("20",)),
        row("資産合計", 1, ("29",), True),
    ]
    result = build_hierarchy(classify_rows(layout(rows)))
    assert result.hierarchy_source == "indentation"
    assert [r.parent_row_id for r in result.rows] == [None, 1, 2, 3, 3, 2, 1, 7, 1]
    assert result.rows[7].parent_path == "Root > B"
    assert result.rows[4].parent_path == "Root > A > Other"
    assert [r.row_id for r in result.rows[2].children] == [4, 5]
    assert [r.label for r in result.tree] == ["Root"]
    assert not result.warnings


def test_skipped_step_is_warned_and_level_counts_ancestors():
    result = build_hierarchy(classify_rows(layout([row("Root", 2), row("Child", 5, ("10",))])))
    assert result.rows[1].level == 1
    assert result.rows[1].parent_row_id == 1
    assert "skipped_indent" in {w.code for w in result.warnings}


def test_first_row_not_least_indented_creates_explicit_forest():
    result = build_hierarchy(classify_rows(layout([row("First", 3), row("Later root", 1)])))
    assert [r.parent_row_id for r in result.rows] == [None, None]
    assert len(result.tree) == 2
    assert "first_row_not_least_indented" in {w.code for w in result.warnings}


def test_flat_fallback_is_partial_and_warned():
    rows = [
        row("Root"),
        row("Group"),
        row("Gross", raws=("10",)),
        row("減価償却累計額", raws=("△1",)),
        row("Gross（純額）", raws=("9",), rule=True),
        row("Group合計", raws=("9",), rule=True),
        row("Other group"),
        row("Leaf", raws=("2",)),
        row("資産合計", raws=("11",), rule=True),
    ]
    result = build_hierarchy(classify_rows(layout(rows)))
    assert result.hierarchy_source == "rules_fallback"
    assert [r.parent_row_id for r in result.rows] == [None, 1, 2, 3, 3, 2, 1, 7, 1]
    assert "insufficient_indentation" in {w.code for w in result.warnings}


def test_unlabeled_value_row_and_missing_indent_are_kept():
    result = build_hierarchy(
        classify_rows(layout([row("Root", 0), row("Section", 1), row("", None, ("12",))]))
    )
    assert result.rows[-1].parent_row_id == 2
    assert result.rows[-1].label == ""
    assert {"unlabeled_value_row", "missing_indent"} <= {w.code for w in result.warnings}


def test_empty_body():
    result = build_hierarchy(classify_rows(layout()))
    assert result.rows == result.tree == ()
    assert result.hierarchy_source == "rules_fallback" and result.warnings
