"""Pure metadata tests, including the P4 unit-heading regression."""

from dataclasses import replace

import pytest

from parser.layout_types import Column
from parser.metadata import clean_column_heading, extract_metadata
from test_hierarchy import layout, row


def test_clean_unit_line_without_changing_other_heading_text():
    heading = "（単位：千円）\n当連結会計年度\n(2026年３月31日)"
    cleaned = clean_column_heading(heading, r"\(単位:(?P<unit>千円)\)")
    assert cleaned == "当連結会計年度\n(2026年３月31日)"
    assert heading.startswith("（単位：千円）")


@pytest.mark.parametrize("unit,multiplier", [("千円", 1000), ("百万円", 1000000), ("円", 1)])
def test_unit_metadata_without_scaling(unit, multiplier):
    page = layout([row(f"（単位：{unit}）", zone="header"), row("Title", zone="header"),
                   row("（訂正後）", zone="header"), row("- 4 -", zone="footer")])
    result = extract_metadata(page)
    assert (result.page.unit, result.page.unit_multiplier) == (unit, multiplier)
    assert result.page.correction_marker == "訂正後"
    assert result.page.printed_page_number == 4
    assert result.page.title_lines == ("Title",)


def test_missing_metadata_is_none_and_body_is_not_metadata():
    result = extract_metadata(layout([row("（単位：千円）")]))
    assert result.page.title is None
    assert result.page.correction_marker is None
    assert result.page.unit is result.page.unit_multiplier is result.page.printed_page_number is None


@pytest.mark.parametrize("dates,expected", [
    ([(2025, 3, 31), (2026, 3, 31)], ["previous_year", "current_year"]),
    ([(2026, 3, 31), (2025, 3, 31)], ["current_year", "previous_year"]),
    ([(2025, 3, 31)], ["value_1"]),
    ([(2025, 3, 31), (2026, 3, 31), (2027, 3, 31)], ["value_1", "value_2", "value_3"]),
    ([None, (2026, 3, 31)], ["value_1", "value_2"]),
    ([(2025, 3, 31), (2025, 3, 31)], ["value_1", "value_2"]),
    ([], []),
])
def test_column_roles(dates, expected):
    columns = [Column(i, 200 + 100 * i, f"Column {i}", date) for i, date in enumerate(dates)]
    result = extract_metadata(layout(columns=columns))
    assert [c.role for c in result.columns] == expected
    assert bool(result.warnings) is (not expected or expected[0].startswith("value_"))


def test_unit_cleanup_is_applied_to_exported_headings():
    page = layout()
    columns = (page.columns[0], replace(page.columns[1], heading="（単位：千円）\n当連結会計年度\n(2026年３月31日)"))
    result = extract_metadata(replace(page, columns=columns))
    assert result.columns[1].heading == "当連結会計年度\n(2026年３月31日)"
    assert page.columns[1].heading == "Later\n(2026年3月31日)"


def test_date_only_header_is_not_a_title_when_columns_are_missing():
    result = extract_metadata(layout([row("（２０２６年３月３１日）", zone="header")], columns=[]))
    assert result.page.title is None
