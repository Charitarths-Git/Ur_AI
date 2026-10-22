"""Label-free synthetic accounting, tolerance and hypothesis interval tests."""

from dataclasses import replace

import pytest

from parser.evaluation.accounting import AccountRow, accounting_checks, accounting_summary

COLS = ("value_1",)


def a(ident, parent, kind, value, raw=None):
    return AccountRow(ident, parent, kind, (value,), (str(value) if raw is None and value is not None else raw or "",))


def nested():
    return (a("root", None, "header", None), a("section", "root", "header", None),
            a("gross", "section", "line_item", 100), a("contra", "gross", "contra", -30, "△30"),
            a("net", "gross", "net", 70), a("nil", "section", "line_item", None, "－"),
            a("subtotal", "section", "subtotal", 70), a("total", "root", "total", 70))


def test_nested_contributions_use_net_not_gross_or_contra():
    rows = nested()
    assert "label" not in rows[0].__dataclass_fields__
    checks = accounting_checks(rows, COLS)
    evaluable = [c for c in checks if c.kind != "balance"]
    assert all(c.status == "exact" for c in evaluable)
    subtotal = next(c for c in checks if c.row_id == "subtotal")
    assert subtotal.expected == 70 and subtotal.n == 2
    total = next(c for c in checks if c.row_id == "total")
    assert total.n == 1 and total.expected == 70
    assert accounting_summary(checks)["pass_rate"] == 1


@pytest.mark.parametrize("raw", ["abc", "", "1.5"])
def test_invalid_or_empty_null_is_not_zero(raw):
    rows = tuple(replace(r, raws=(raw,)) if r.row_id == "nil" else r for r in nested())
    check = next(c for c in accounting_checks(rows, COLS) if c.row_id == "subtotal")
    assert check.status == "not_evaluable" and check.expected is None


@pytest.mark.parametrize("printed,status", [(30, "exact"), (32, "within_tolerance"), (33, "fail")])
def test_tolerance_boundary_n_and_n_plus_one(printed, status):
    rows = (a("1", "root", "line_item", 10), a("2", "root", "line_item", 20),
            a("s", "root", "subtotal", printed), a("root", None, "header", None))
    check = next(c for c in accounting_checks(rows, COLS) if c.row_id == "s")
    assert check.n == 2 and check.tolerance == 2 and check.status == status
    strict = next(c for c in accounting_checks(rows, COLS, lambda n: 0) if c.row_id == "s")
    assert strict.status == ("exact" if printed == 30 else "fail")


@pytest.mark.parametrize("printed,inside", [(69, True), (70, True), (68, False), (71, False)])
def test_mixed_sign_truncation_interval_boundaries(printed, inside):
    rows = tuple(replace(r, values=(printed,), raws=(str(printed),)) if r.row_id == "net" else r for r in nested())
    check = next(c for c in accounting_checks(rows, COLS) if c.kind == "net")
    assert (check.truncation_lower, check.truncation_upper) == (-1, 0)
    assert check.truncation_consistent is inside
    assert check.status in {"exact", "within_tolerance"}  # diagnostic never gates status


@pytest.mark.parametrize("printed,inside", [(30, True), (31, True), (32, False)])
def test_positive_truncation_interval_boundaries(printed, inside):
    rows = (a("1", None, "line_item", 10), a("2", None, "line_item", 20), a("s", None, "subtotal", printed))
    check = next(c for c in accounting_checks(rows, COLS) if c.row_id == "s")
    assert (check.truncation_lower, check.truncation_upper) == (0, 1)
    assert check.truncation_consistent is inside


def test_requested_negative_only_diagnostic_is_not_a_universal_pass_rule():
    rows = (a("1", None, "line_item", -10), a("2", None, "line_item", -20), a("s", None, "subtotal", -30))
    check = next(c for c in accounting_checks(rows, COLS) if c.row_id == "s")
    assert check.status == "exact" and check.truncation_consistent is False
    assert (check.truncation_lower, check.truncation_upper) == (-2, -1)


@pytest.mark.parametrize("two", [False, True])
def test_balance_identity(two):
    rows = (a("a", None, "total", 100),)
    if two:
        rows += (a("b", None, "total", 100),)
    check = next(c for c in accounting_checks(rows, COLS) if c.kind == "balance")
    assert check.status == ("exact" if two else "not_applicable")


def test_header_without_subtotal_cannot_contribute_guessed_sum():
    rows = (a("h", None, "header", None), a("leaf", "h", "line_item", 20), a("t", None, "total", 20))
    check = next(c for c in accounting_checks(rows, COLS) if c.row_id == "t")
    assert check.status == "not_evaluable"


def test_empty_checks_have_no_pass_rate():
    summary = accounting_summary(accounting_checks((), COLS))
    assert summary["pass_rate"] is None and summary["evaluable"] == 0
