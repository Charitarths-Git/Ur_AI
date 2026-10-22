"""Pure metadata tests, including the P4 unit-heading regression."""

from parser.metadata import clean_column_heading


def test_clean_unit_line_without_changing_other_heading_text():
    heading = "（単位：千円）\n当連結会計年度\n(2026年３月31日)"
    cleaned = clean_column_heading(heading, r"\(単位:(?P<unit>千円)\)")
    assert cleaned == "当連結会計年度\n(2026年３月31日)"
    assert heading.startswith("（単位：千円）")
