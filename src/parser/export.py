"""Page pipeline and deterministic CSV/JSON serializers; only the backend reads PDFs."""

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from parser.classify import ParseWarning, classify_rows
from parser.hierarchy import TreeRow, build_hierarchy
from parser.layout_types import LayoutConfig, PageLayout
from parser.metadata import PageMetadata, RoleColumn, extract_metadata
from parser.normalize import parse_amount
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page
from parser.rules import JA_FINANCIAL_STATEMENT, RuleSet


@dataclass(frozen=True)
class Source:
    file: str
    page: int
    backend: str


@dataclass(frozen=True)
class ParsedPage:
    source: Source
    rows: tuple[TreeRow, ...]
    tree: tuple[TreeRow, ...]
    metadata: PageMetadata
    columns: tuple[RoleColumn, ...]
    warnings: tuple[ParseWarning, ...]
    hierarchy_source: str


def parse_layout(
    layout: PageLayout,
    source_name: str,
    page_number: int = 1,
    backend: str = "pymupdf",
    rules: RuleSet = JA_FINANCIAL_STATEMENT,
) -> ParsedPage:
    """Pure assembly from a P4 layout; source provenance is supplied, never inferred."""
    hierarchy = build_hierarchy(classify_rows(layout, rules))
    metadata = extract_metadata(layout, rules)
    return ParsedPage(
        Source(Path(source_name).name, page_number, backend),
        hierarchy.rows,
        hierarchy.tree,
        metadata.page,
        metadata.columns,
        hierarchy.warnings + metadata.warnings + layout.warnings,
        hierarchy.hierarchy_source,
    )


def parse_page(
    path: str | Path,
    page_number: int = 1,
    layout_config: LayoutConfig = LayoutConfig(),
    rules: RuleSet = JA_FINANCIAL_STATEMENT,
) -> ParsedPage:
    raw = read_pdf_page(path, page_number, layout_config)
    return parse_layout(
        reconstruct_page(raw, layout_config), Path(path).name, page_number, rules=rules
    )


def row_values(row: TreeRow, columns: tuple[RoleColumn, ...]) -> dict:
    cells = {c.column_index: c for c in row.typed.row.cells}
    values = {}
    for column in columns:
        cell = cells.get(column.index)
        amount = cell.amount if cell else parse_amount("")
        values[column.role] = {
            "raw": cell.raw if cell else "",
            "value": amount.value,
            "status": amount.status,
        }
    return values


def csv_columns(page: ParsedPage) -> list[str]:
    standard = {c.role for c in page.columns} == {"previous_year", "current_year"}
    values = (
        ["previous_year_value", "current_year_value"]
        if standard
        else [c.role for c in page.columns]
    )
    raws = (
        ["prev_raw", "curr_raw"] if standard else [f"raw_{i + 1}" for i in range(len(page.columns))]
    )
    return [
        "label",
        "parent",
        "level",
        "row_type",
        *values,
        "row_id",
        "parent_row_id",
        "parent_path",
        *raws,
    ]


def csv_bytes(page: ParsedPage) -> bytes:
    """UTF-8 BOM, stable LF newlines, integers in printed units and empty null cells."""
    columns = csv_columns(page)
    standard = {c.role for c in page.columns} == {"previous_year", "current_year"}
    roles = ["previous_year", "current_year"] if standard else [c.role for c in page.columns]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    for row in page.rows:
        values = row_values(row, page.columns)
        writer.writerow(
            [
                row.label,
                row.parent,
                row.level,
                row.row_type,
                *(values[role]["value"] for role in roles),
                row.row_id,
                row.parent_row_id,
                row.parent_path,
                *(values[role]["raw"] for role in roles),
            ]
        )
    return stream.getvalue().encode("utf-8-sig")


def json_document(page: ParsedPage) -> dict:
    def node(row):
        return {
            "row_id": row.row_id,
            "label": row.label,
            "row_type": row.row_type,
            "level": row.level,
            "values": row_values(row, page.columns),
            "children": [node(child) for child in row.children],
        }

    return {
        "schema_version": "1.0",
        "source": asdict(page.source),
        "page": {
            "title": page.metadata.title,
            "correction_marker": page.metadata.correction_marker,
            "unit": page.metadata.unit,
            "unit_multiplier": page.metadata.unit_multiplier,
            "printed_page_number": page.metadata.printed_page_number,
        },
        "columns": [
            {
                "index": c.index,
                "role": c.role,
                "heading": c.heading,
                "period_end": date(*c.period_end).isoformat() if c.period_end else None,
            }
            for c in page.columns
        ],
        "hierarchy_source": page.hierarchy_source,
        "warnings": [asdict(warning) for warning in page.warnings],
        "rows": [node(row) for row in page.tree],
    }


def json_bytes(page: ParsedPage) -> bytes:
    return (json.dumps(json_document(page), ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_exports(page: ParsedPage, out_dir: str | Path) -> tuple[Path, Path]:
    """Explicit output I/O boundary; pure serializers above never write files."""
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{Path(page.source.file).stem}_p{page.source.page}"
    csv_path, json_path = directory / f"{stem}.csv", directory / f"{stem}.json"
    csv_path.write_bytes(csv_bytes(page))
    json_path.write_bytes(json_bytes(page))
    return csv_path, json_path
