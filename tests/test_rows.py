"""Synthetic geometry tests plus read-only real-page/GT integration diagnostics."""

import ast
import csv
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from parser.evaluation.perturb import transform
from parser.layout_types import LayoutConfig, RawPage, Rule, Word
from parser.normalize import label_key, parse_period_end
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/balance_sheet_after_correction.pdf"


def word(text, x0, y0, width=40, height=10):
    return Word(text, x0, y0, x0 + width, y0 + height, height)


def synthetic_page(columns=2):
    words = [word("Report", 10, 10, 70), word("9", 85, 10, 5)]
    for i in range(columns):
        words += [
            word(f"Period {chr(65 + i)}", 120 + 100 * i, 25, 60),
            word(f"({2025 + i}年3月31日)", 120 + 100 * i, 40, 72),
        ]
    words += [
        word("Section", 20, 60),
        word("Series", 40, 80, 30),
        word("2", 75, 80, 5),
        word("item", 84, 80, 20),
        word("Second", 40, 100, 60),
        word("Third", 60, 120),
        word("Last", 40, 140),
    ]
    amounts = [("100", "200"), ("25", "△0"), ("－", "1.5"), ("1,234", "2,345")]
    for row, pair in enumerate(amounts):
        y = 80 + row * 20
        for col in range(columns):
            text = pair[col] if col < 2 else str(300 + row)
            width = 12 if row == 1 and col == 0 else max(len(text) * 6, 8)
            right = 200 + col * 100
            words.append(word(text, right - width, y, width))
            if row == 1 and col == 0:
                words.append(word("△", right - width - 7, y, 5))
    # A short thin rule overlaps actual value ink without reaching the x1 centre.
    rules = [
        Rule(170, 95, 190, 95.5, 0.5),
        Rule(110, 112, 310, 124, 12),
        Rule(10, 135, 100, 135.5, 0.5),
    ]
    footer = [word("-", 135, 190, 5), word("7", 145, 190, 5), word("-", 155, 190, 5)]
    return RawPage(500, 240, footer + words, rules)


@pytest.fixture(scope="module")
def real_page():
    return read_pdf_page(PDF)


def body(layout):
    return [r for r in layout.rows if r.zone == "body"]


def signature(layout):
    return (
        tuple(
            (
                r.zone,
                r.label,
                r.indent_step,
                r.rule_above,
                tuple(
                    (c.column_index, c.raw, c.amount.value, c.amount.status, c.amount.negative)
                    for c in r.cells
                ),
            )
            for r in layout.rows
        ),
        tuple((c.index, c.heading, c.period_end) for c in layout.columns),
    )


def test_synthetic_cells_labels_zones_and_evidence():
    page = synthetic_page()
    layout = reconstruct_page(page)
    rows = body(layout)
    assert len(layout.columns) == 2
    assert [r.label for r in rows] == ["Section", "Series 2 item", "Second", "Third", "Last"]
    assert [r.indent_step for r in rows] == [0, 1, 1, 2, 1]
    assert not rows[0].cells
    assert [c.raw for c in rows[2].cells] == ["△25", "△0"]
    assert rows[2].cells[0].amount.value == -25
    assert rows[2].cells[1].amount.negative
    assert rows[3].cells[0].amount.status == "nil"
    assert rows[3].cells[1].amount.status == "invalid"
    assert rows[3].cells[1].amount.value is None
    assert rows[2].rule_above  # partial horizontal overlap is sufficient
    assert not rows[-1].rule_above  # label-only rule and shading are not value rules
    assert [r.zone for r in layout.rows][-1] == "footer"
    assert layout.rows[-1].cells == ()
    assert [c.period_end for c in layout.columns] == [(2025, 3, 31), (2026, 3, 31)]


def test_jittered_baselines_and_different_font_sizes():
    page = synthetic_page()
    varied = []
    for i, w in enumerate(page.words):
        h = (8, 10, 12)[i % 3]
        centre = (w.y0 + w.y1) / 2 + (i % 3 - 1) * 0.3
        varied.append(replace(w, y0=centre - h / 2, y1=centre + h / 2, size=h))
    before = reconstruct_page(page)
    after = reconstruct_page(replace(page, words=varied))
    assert [(r.label, [c.raw for c in r.cells], r.zone, r.indent_step) for r in after.rows] == [
        (r.label, [c.raw for c in r.cells], r.zone, r.indent_step) for r in before.rows
    ]


@pytest.mark.parametrize(
    "mode", ["shuffle", "translate", "scale_small", "scale_large", "combined", "jitter"]
)
@pytest.mark.parametrize("source", ["synthetic", "real"])
def test_invariance(source, mode, real_page):
    page = synthetic_page() if source == "synthetic" else real_page
    original = reconstruct_page(page)
    changed = reconstruct_page(transform(page, mode))
    assert signature(changed) == signature(original)
    if mode.startswith("scale") or mode == "combined":
        factor = {"scale_small": 0.45, "scale_large": 2.75, "combined": 1.7}[mode]
        assert changed.thresholds.row_tolerance == pytest.approx(
            original.thresholds.row_tolerance * factor
        )
    elif mode == "translate":
        assert changed.indent_centres == pytest.approx([x - 240 for x in original.indent_centres])


def test_three_value_columns():
    layout = reconstruct_page(synthetic_page(columns=3))
    assert len(layout.columns) == 3
    assert all(len(r.cells) == 3 for r in body(layout) if r.cells)
    assert [c.period_end for c in layout.columns] == [(2025, 3, 31), (2026, 3, 31), (2027, 3, 31)]


def test_no_body_and_empty_inputs():
    empty = reconstruct_page(RawPage(500, 600))
    assert empty.rows == empty.columns == empty.indent_centres == ()
    page = RawPage(500, 600, [word("Title", 20, 10), word("(2025年3月31日)", 120, 40)])
    layout = reconstruct_page(page)
    assert all(r.zone == "header" and not r.cells and r.indent_step is None for r in layout.rows)
    assert not layout.columns
    blank = RawPage(500, 600, [word("\u3000", 20, 10), word("broken", 20, 40, height=0)])
    assert not reconstruct_page(blank).rows


def test_no_date_fallback_and_label_only_last_row():
    page = synthetic_page()
    words = [w for w in page.words if "年" not in w.text]
    words += [word("Trailing label", 40, 165)]
    layout = reconstruct_page(replace(page, words=words))
    assert next(r for r in layout.rows if r.label == "Section").zone == "header"
    assert next(r for r in layout.rows if r.label == "Series 2 item").zone == "body"
    assert next(r for r in layout.rows if r.label == "Trailing label").zone == "footer"
    assert all(c.period_end is None for c in layout.columns)


def test_invalid_last_value_row_is_retained():
    page = synthetic_page()
    words = list(page.words) + [
        word("Invalid final", 40, 165, 70),
        word("oops", 176, 165, 24),
        word("1.5", 282, 165, 18),
    ]
    last = body(reconstruct_page(replace(page, words=words)))[-1]
    assert last.label == "Invalid final"
    assert [c.amount.status for c in last.cells] == ["invalid", "invalid"]


def test_distinct_supporting_rows_and_configurable_minimum():
    page = RawPage(300, 200, [word("Line", 10, 40), word("100", 182, 40, 18)])
    assert not reconstruct_page(page).columns
    layout = reconstruct_page(page, LayoutConfig(column_min_support=1))
    assert len(layout.columns) == 1
    assert body(layout)[0].cells[0].amount.value == 100
    # Several candidates at the same right edge on one row still support just one row.
    repeated = replace(page, words=page.words + (word("1", 194, 40, 6), word("2", 188, 40, 12)))
    assert not reconstruct_page(repeated).columns


def test_split_sign_gap_limit():
    page = synthetic_page()
    words = [replace(w, x0=w.x0 - 30, x1=w.x1 - 30) if w.text == "△" else w for w in page.words]
    row = next(r for r in body(reconstruct_page(replace(page, words=words))) if "Second" in r.label)
    assert "△" in row.label
    assert row.cells[0].raw == "25"


def test_frozen_output_and_pure_input():
    page = synthetic_page()
    before = page.words, page.rules
    layout = reconstruct_page(page)
    assert (page.words, page.rules) == before
    with pytest.raises(FrozenInstanceError):
        layout.rows[0].label = "changed"
    with pytest.raises(FrozenInstanceError):
        layout.columns[0].x1_centre = 0
    assert not {"parent", "parent_path", "level", "row_type"} & set(
        layout.rows[0].__dataclass_fields__
    )


def test_backend_is_only_package_pymupdf_importer():
    importers = []
    for path in (ROOT / "src/parser").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                a.name in {"pymupdf", "fitz"} for a in node.names
            ):
                importers.append(path.name)
            elif isinstance(node, ast.ImportFrom) and node.module in {"pymupdf", "fitz"}:
                importers.append(path.name)
    assert importers == ["pdf_backend.py"]


def gt_report(layout, gt):
    """Informational comparison only; never used by production reconstruction."""
    rows = body(layout)
    exact = sum(r.label == g["label"] for r, g in zip(rows, gt, strict=True))
    spaces = sum(any(char.isspace() for char in r.label) for r in rows)
    rule = Counter((g["row_type"], r.rule_above) for r, g in zip(rows, gt, strict=True))
    indent = Counter((r.indent_step, int(g["level"])) for r, g in zip(rows, gt, strict=True))
    lines = [
        f"Exact label matches: {exact}/{len(gt)}; labels with internal spaces: {spaces}.",
        "",
        "| GT row_type | rule_above=False | rule_above=True |",
        "|---|---:|---:|",
    ]
    for kind in sorted({g["row_type"] for g in gt}):
        lines.append(f"| {kind} | {rule[kind, False]} | {rule[kind, True]} |")
    levels = sorted({int(g["level"]) for g in gt})
    lines += [
        "",
        "| indent_step | " + " | ".join(f"GT level {i}" for i in levels) + " |",
        "|---|" + "---:|" * len(levels),
    ]
    for step in sorted({r.indent_step for r in rows}):
        lines.append(f"| {step} | " + " | ".join(str(indent[step, i]) for i in levels) + " |")
    return "\n".join(lines)


def test_real_page_matches_gt(real_page):
    layout = reconstruct_page(real_page)
    with (ROOT / "data/gt/page4.csv").open(encoding="utf-8-sig", newline="") as stream:
        gt = list(csv.DictReader(stream))
    with (ROOT / "data/gt/page4_meta.json").open(encoding="utf-8-sig") as stream:
        meta = json.load(stream)
    rows = body(layout)
    assert len(rows) == len(gt)
    assert len(layout.columns) == 2
    for row, expected in zip(rows, gt, strict=True):
        assert label_key(row.label) == label_key(expected["label"]), expected["row_id"]
        if expected["row_type"] == "header":
            assert not row.cells
            continue
        assert [c.column_index for c in row.cells] == [0, 1]
        for cell, raw_col, val_col in zip(
            row.cells,
            ["prev_raw", "curr_raw"],
            ["previous_year_value", "current_year_value"],
            strict=True,
        ):
            assert cell.raw == expected[raw_col], expected["row_id"]
            value = int(expected[val_col]) if expected[val_col] else None
            assert cell.amount.value == value, expected["row_id"]
    for column, key in zip(layout.columns, ["previous", "current"], strict=True):
        heading = meta["period_headings"][key] + meta["period_end_dates"][key]
        assert column.period_end == parse_period_end(heading)
    # Exact label matches and GT cross-tabs are reported, never asserted.
    print(gt_report(layout, gt))


@pytest.mark.parametrize("script", ["dump_rows.py", "inspect_pdf.py"])
def test_cli_without_encoding_environment(script):
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [sys.executable, "-X", "utf8=0", str(ROOT / "scripts" / script), str(PDF)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert "資産の部" in result.stdout.decode("utf-8")
