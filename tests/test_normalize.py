"""Pure normalization cases and a read-only round trip against verified GT."""

import csv
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from parser.normalize import AmountResult, label_key, labels_equal, parse_amount, parse_period_end


@pytest.mark.parametrize(
    "raw,status,value,negative",
    [
        ("123", "ok", 123, False),
        ("0", "ok", 0, False),
        ("00012", "ok", 12, False),
        ("2,002,429", "ok", 2002429, False),
        ("２００２４２９", "ok", 2002429, False),
        ("２，００２，４２９", "ok", 2002429, False),
        ("1，234", "ok", 1234, False),
        ("1,23", "ok", 123, False),
        ("1234,567", "ok", 1234567, False),
        ("1,2,3", "ok", 123, False),
        ("△2,979", "ok", -2979, True),
        ("▲２，９７９", "ok", -2979, True),
        ("-123", "ok", -123, True),
        ("−123", "ok", -123, True),
        ("－１２３", "ok", -123, True),
        ("(123)", "ok", -123, True),
        ("（１，２３４）", "ok", -1234, True),
        ("( 123 )", "ok", -123, True),
        ("- \u3000123", "ok", -123, True),
        ("\u3000\u00a0２，００２，４２９\t\n", "ok", 2002429, False),
        ("△0", "ok", 0, True),
        ("▲0", "ok", 0, True),
        ("-0", "ok", 0, True),
        ("（０）", "ok", 0, True),
        ("", "empty", None, False),
        (" \t\n\u3000\u00a0", "empty", None, False),
        ("1.5", "invalid", None, False),
        ("１．５", "invalid", None, False),
        ("12-3", "invalid", None, False),
        ("△-5", "invalid", None, False),
        ("--5", "invalid", None, False),
        ("−▲5", "invalid", None, False),
        ("(△5)", "invalid", None, False),
        ("-(5)", "invalid", None, False),
        ("12千円", "invalid", None, False),
        ("12円", "invalid", None, False),
        ("abc", "invalid", None, False),
        ("12 34", "invalid", None, False),
        ("1, 234", "invalid", None, False),
        ("+123", "invalid", None, False),
        ("123%", "invalid", None, False),
        ("1_234", "invalid", None, False),
        ("…", "invalid", None, False),
        ("･･･", "invalid", None, False),
        ("(123", "invalid", None, False),
        ("123)", "invalid", None, False),
        ("((123))", "invalid", None, False),
        ("()", "invalid", None, False),
        ("△", "invalid", None, False),
        (",123", "invalid", None, False),
        ("123,", "invalid", None, False),
        ("1,,234", "invalid", None, False),
        (None, "invalid", None, False),
        (123, "invalid", None, False),
        (1.5, "invalid", None, False),
    ],
)
def test_parse_amount(raw, status, value, negative):
    result = parse_amount(raw)
    assert isinstance(result, AmountResult)
    assert result.raw == raw
    assert result.status == status
    assert result.value == value
    assert result.negative is negative
    assert result.value is None or type(result.value) is int
    if status == "invalid":
        assert result.note


@pytest.mark.parametrize("dash", ["－", "―", "—", "–", "−", "‐", "ー", "-"])
@pytest.mark.parametrize("form", ["single", "run", "spaced"])
def test_nil_markers(dash, form):
    raw = {"single": dash, "run": dash * 3, "spaced": f"\u3000{dash} \t{dash}\u00a0"}[form]
    result = parse_amount(raw)
    assert (result.status, result.value, result.negative) == ("nil", None, False)
    assert result.raw == raw


@pytest.mark.parametrize("dash", ["－", "―", "—", "–", "−", "‐", "ー", "-"])
def test_each_nil_dash_before_digits_is_negative(dash):
    result = parse_amount(dash + "１２３")
    assert (result.status, result.value, result.negative) == ("ok", -123, True)


def test_mixed_nil_dash_run():
    result = parse_amount(" － —\u3000−ー- ")
    assert (result.status, result.value, result.negative) == ("nil", None, False)


@pytest.mark.parametrize("raw", ["△0", "▲0", "－０", "（０）"])
def test_negative_zero_note(raw):
    result = parse_amount(raw)
    assert (result.status, result.value, result.negative) == ("ok", 0, True)
    assert result.note == "negative zero printed"


@pytest.mark.parametrize("raw", ["1,23", "1234,567", "1,2345", "1,2,3"])
def test_nonstandard_comma_grouping_is_informational(raw):
    result = parse_amount(raw)
    assert result.status == "ok"
    assert "comma grouping" in result.note


@pytest.mark.parametrize("raw", ["12345", "12,345", "123,456", "１，２３４"])
def test_normal_grouping_has_no_note(raw):
    assert parse_amount(raw).note == ""


@pytest.mark.parametrize("prefix", ["", "△"])
def test_very_long_integer(prefix):
    # Exceeds Python's usual 4,300-digit string-to-int limit; no global changes.
    raw = prefix + "9" * 10000
    result = parse_amount(raw)
    expected = 10 ** 10000 - 1
    assert result.value == (-expected if prefix else expected)
    assert result.raw == raw
    assert result.status == "ok"
    assert result.negative is bool(prefix)
    assert type(result.value) is int


def test_amount_result_is_frozen():
    result = parse_amount("123")
    with pytest.raises(FrozenInstanceError):
        result.value = 0


@pytest.mark.parametrize(
    "label,expected",
    [
        ("建物及び構築物 （純額）", "建物及び構築物(純額)"),
        ("建物及び構築物（純額）", "建物及び構築物(純額)"),
        ("\u3000その他\u00a0\t(純額)\n", "その他(純額)"),
        ("ＡＢＣ１２３", "ABC123"),
        ("A \u030a", "Å"),
        ("か\u3000\u3099", "が"),
        ("", ""),
        (" \t\u3000\u00a0", ""),
    ],
)
def test_label_key_and_idempotence(label, expected):
    assert label_key(label) == expected
    assert label_key(label_key(label)) == label_key(label)


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("建物及び構築物 （純額）", "建物及び構築物（純額）", True),
        ("リース資産（純額）", "リース資産(純額)", True),
        ("そ の\u3000他", "その他", True),
        ("資産", "資産合計", False),
        ("abc", "ABC", False),
    ],
)
def test_labels_equal(a, b, expected):
    assert labels_equal(a, b) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("(2025 年３月 31 日)", (2025, 3, 31)),
        ("（２０２６年３月３１日）", (2026, 3, 31)),
        ("前連結会計年度\n(2025\u3000年\u00a0３ 月\t31 日)", (2025, 3, 31)),
        ("2024年2月29日", (2024, 2, 29)),
        ("2025年2月29日", None),
        ("2025年13月31日", None),
        ("2025年３月", None),
        ("令和７年３月31日", None),
        ("12025年3月31日", None),
        ("2025年3月31日と2026年3月31日", (2025, 3, 31)),
        ("abc", None),
        (None, None),
    ],
)
def test_parse_period_end(text, expected):
    assert parse_period_end(text) == expected


def test_verified_gt_amount_round_trip():
    """Read every raw cell as utf-8-sig; never access a PDF or write GT."""
    path = Path(__file__).resolve().parents[1] / "data/gt/page4.csv"
    before = path.read_bytes()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            for raw_col, value_col in [("prev_raw", "previous_year_value"),
                                       ("curr_raw", "current_year_value")]:
                raw = row[raw_col]
                result = parse_amount(raw)
                expected = int(row[value_col]) if row[value_col] != "" else None
                message = f'{row["row_id"]} {row["label"]} {raw_col}={raw!r}'
                assert result.raw == raw, message
                assert result.value == expected, message
                assert result.status == ("empty" if raw == "" else
                                         "nil" if raw == "－" else "ok"), message
                assert result.negative is raw.startswith("△"), message
    assert path.read_bytes() == before
