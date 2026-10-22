"""Pure metadata helpers; language-specific patterns are supplied by the caller."""

import re
from dataclasses import dataclass

from parser.classify import ParseWarning
from parser.layout_types import PageLayout
from parser.normalize import label_key
from parser.rules import JA_FINANCIAL_STATEMENT, RuleSet


def clean_column_heading(heading: str, unit_pattern: str) -> str:
    """Remove whole unit lines from metadata headings, preserving other text.

    P4 keeps its original geometric heading evidence. Apply the caller's pattern
    to comparison keys only, so emitted headings keep printed characters.
    """
    return "\n".join(line for line in heading.splitlines()
                     if not re.fullmatch(unit_pattern, label_key(line)))


@dataclass(frozen=True)
class PageMetadata:
    title_lines: tuple[str, ...] | None
    correction_marker: str | None
    unit: str | None
    unit_multiplier: int | None
    printed_page_number: int | None

    @property
    def title(self) -> str | None:
        return "\n".join(self.title_lines) if self.title_lines else None


@dataclass(frozen=True)
class RoleColumn:
    index: int
    role: str
    heading: str
    period_end: tuple[int, int, int] | None


@dataclass(frozen=True)
class MetadataResult:
    page: PageMetadata
    columns: tuple[RoleColumn, ...]
    warnings: tuple[ParseWarning, ...]


def extract_metadata(
    layout: PageLayout, rules: RuleSet = JA_FINANCIAL_STATEMENT
) -> MetadataResult:
    """Read header/footer evidence only; absent fields stay None, units never scale cells.

    Remaining header lines form the title after known markers, unit lines and
    column-heading text are excluded. Keep printed title/heading characters.
    """
    columns = sorted(layout.columns, key=lambda c: c.x1_centre)
    warnings = []
    dates = [c.period_end for c in columns]
    dated_pair = len(columns) == 2 and all(d is not None for d in dates) and dates[0] != dates[1]
    if not dated_pair:
        warnings.append(ParseWarning("ambiguous_column_roles", "columns lack a unique two-date previous/current mapping"))
    roles = []
    for i, column in enumerate(columns):
        if dated_pair:
            role = "previous_year" if column.period_end == min(dates) else "current_year"
        else:
            role = f"value_{i + 1}"
        roles.append(RoleColumn(column.index, role,
                                clean_column_heading(column.heading, rules.unit_pattern), column.period_end))
    heading_keys = sorted({label_key(line) for c in roles for line in c.heading.splitlines()
                           if label_key(line)}, key=lambda key: (-len(key), key))
    marker = unit = multiplier = printed_number = None
    titles = []
    for row in layout.rows:
        if row.zone not in {"header", "footer"}:
            continue
        key = label_key(row.label)
        if row.zone == "footer":
            match = re.fullmatch(rules.page_number_pattern, key)
            if match and printed_number is None:
                printed_number = int(match.group("page"))
            continue
        correction = next((value for pattern, value in rules.correction_markers
                           if key == label_key(pattern)), None)
        if correction is not None:
            if marker is None:
                marker = correction
            elif marker != correction:
                warnings.append(ParseWarning("conflicting_correction_markers", "multiple correction markers found"))
            continue
        match = re.fullmatch(rules.unit_pattern, key)
        if match:
            found_unit = match.group("unit")
            if unit is None:
                unit = found_unit
                multiplier = next((value for text, value in rules.unit_multipliers.items()
                                   if label_key(text) == found_unit), None)
            elif unit != found_unit:
                warnings.append(ParseWarning("conflicting_units", "multiple unit strings found"))
            continue
        remainder = key
        for heading_key in heading_keys:
            remainder = remainder.replace(heading_key, "")
        if remainder:
            titles.append(row.label)
    return MetadataResult(PageMetadata(tuple(titles) if titles else None, marker, unit, multiplier,
                                       printed_number), tuple(roles), tuple(warnings))
