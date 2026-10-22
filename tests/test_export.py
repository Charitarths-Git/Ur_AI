"""Pure export tests, read-only GT integration, transformations and ablation."""

import csv
import io
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from test_hierarchy import layout, row
from test_rows import transform

from parser.evaluation.perturb import flatten_indentation
from parser.export import csv_bytes, csv_columns, json_bytes, parse_layout, parse_page, row_values
from parser.normalize import parse_period_end
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/balance_sheet_after_correction.pdf"


@pytest.fixture(scope="module")
def raw_page():
    return read_pdf_page(PDF)


@pytest.fixture(scope="module")
def parsed(raw_page):
    return parse_layout(reconstruct_page(raw_page), PDF.name)


def ground_truth():
    with (ROOT / "data/gt/page4.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def expected_parent_ids(gt):
    paths = {}
    parents = []
    for i, r in enumerate(gt, 1):
        path = tuple(r["parent_path"].split(" > ")) if r["parent_path"] else ()
        parents.append(paths.get(path))
        paths[path + (r["label"],)] = i
    return parents


def comparison_counts(page, gt):
    counts = Counter()
    for r, g, pid in zip(page.rows, gt, expected_parent_ids(gt), strict=True):
        for field in ["label", "parent", "parent_path", "row_type"]:
            counts[field] += getattr(r, field) == g[field]
        counts["parent_row_id"] += r.parent_row_id == pid
        counts["level"] += r.level == int(g["level"])
        values = row_values(r, page.columns)
        for role, prefix in [("previous_year", "prev"), ("current_year", "curr")]:
            expected = int(g[role + "_value"]) if g[role + "_value"] else None
            counts[role + "_value"] += values[role]["value"] == expected
            counts[prefix + "_raw"] += values[role]["raw"] == g[prefix + "_raw"]
    return dict(counts)



def test_real_page_all_fields_and_metadata_match_gt(parsed):
    gt = ground_truth()
    assert len(parsed.rows) == len(gt)
    assert all(count == len(gt) for count in comparison_counts(parsed, gt).values())
    with (ROOT / "data/gt/page4_meta.json").open(encoding="utf-8-sig") as f:
        meta = json.load(f)
    assert parsed.metadata.unit == meta["unit"]
    assert parsed.metadata.correction_marker == meta["correction_marker"]
    assert parsed.metadata.printed_page_number == meta["page_number"]
    for column, key in zip(parsed.columns, ["previous", "current"], strict=True):
        assert column.period_end == parse_period_end(meta["period_end_dates"][key])
    assert parsed.hierarchy_source == "indentation"
    print("Field matches:", comparison_counts(parsed, gt))
    print("Real-page warnings:", parsed.warnings)


@pytest.mark.parametrize(
    "mode", ["shuffle", "translate", "scale_small", "scale_large", "combined", "jitter"]
)
def test_pipeline_byte_invariance(raw_page, parsed, mode):
    changed = parse_layout(reconstruct_page(transform(raw_page, mode)), PDF.name)
    assert csv_bytes(changed) == csv_bytes(parsed)
    assert json_bytes(changed) == json_bytes(parsed)


def test_flat_indent_ablation(raw_page):
    changed = parse_layout(reconstruct_page(flatten_indentation(raw_page)), PDF.name)
    gt = ground_truth()
    assert changed.hierarchy_source == "rules_fallback"
    assert changed.warnings
    assert [r.row_type for r in changed.rows] == [r["row_type"] for r in gt]
    for r, g in zip(changed.rows, gt, strict=True):
        values = row_values(r, changed.columns)
        for role in ["previous_year", "current_year"]:
            expected = int(g[role + "_value"]) if g[role + "_value"] else None
            assert values[role]["value"] == expected
    # Parent agreement is a diagnostic, not an ablation accuracy assertion.
    parents = expected_parent_ids(gt)
    print(
        "Ablation parents correct:",
        sum(r.parent_row_id == p for r, p in zip(changed.rows, parents, strict=True)),
    )
    print(
        "Ablation errors:",
        [
            (r.row_id, r.label, g["row_type"], r.parent_row_id, p)
            for r, g, p in zip(changed.rows, gt, parents, strict=True)
            if r.parent_row_id != p
        ],
    )


def flatten_json(nodes, parent=None, ancestors=()):
    result = []
    for node in nodes:
        result.append((node, parent, ancestors))
        result.extend(flatten_json(node["children"], node, ancestors + (node["label"],)))
    return result


def test_csv_schema_json_tree_nulls_and_determinism(parsed):
    data = csv_bytes(parsed)
    assert data.startswith(b"\xef\xbb\xbf")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    assert reader.fieldnames == [
        "label",
        "parent",
        "level",
        "row_type",
        "previous_year_value",
        "current_year_value",
        "row_id",
        "parent_row_id",
        "parent_path",
        "prev_raw",
        "curr_raw",
    ]
    rows = list(reader)
    doc = json.loads(json_bytes(parsed))
    assert doc["schema_version"] == "1.0"
    assert doc["source"] == {"file": PDF.name, "page": 1, "backend": "pymupdf"}
    for (node, parent, ancestors), flat in zip(flatten_json(doc["rows"]), rows, strict=True):
        assert str(node["row_id"]) == flat["row_id"]
        assert node["label"] == flat["label"]
        assert node["row_type"] == flat["row_type"]
        assert str(node["level"]) == flat["level"]
        assert (str(parent["row_id"]) if parent else "") == flat["parent_row_id"]
        assert (parent["label"] if parent else "") == flat["parent"]
        assert " > ".join(ancestors) == flat["parent_path"]
        for role, raw_key in [("previous_year", "prev_raw"), ("current_year", "curr_raw")]:
            value = node["values"][role]
            assert value["raw"] == flat[raw_key]
            assert (str(value["value"]) if value["value"] is not None else "") == flat[
                role + "_value"
            ]
            if value["raw"] == "－":
                assert value["value"] is None and value["status"] == "nil"
    assert csv_bytes(parsed) == data
    assert json_bytes(parsed) == json_bytes(parsed)
    assert b"\\u8cc7" not in json_bytes(parsed)
    assert str(ROOT).encode("utf-8") not in json_bytes(parsed)


def test_invalid_status_and_generic_value_columns():
    base = layout([row("Root", 0), row("Invalid", 1, ("1.5", "－"))])
    generic = replace(base, columns=tuple(replace(c, period_end=None) for c in base.columns))
    page = parse_layout(generic, "synthetic.pdf")
    assert csv_columns(page) == [
        "label",
        "parent",
        "level",
        "row_type",
        "value_1",
        "value_2",
        "row_id",
        "parent_row_id",
        "parent_path",
        "raw_1",
        "raw_2",
    ]
    doc = json.loads(json_bytes(page))
    invalid = doc["rows"][0]["children"][0]["values"]
    assert invalid["value_1"] == {"raw": "1.5", "value": None, "status": "invalid"}
    assert invalid["value_2"]["status"] == "nil"


def test_reversed_column_dates_map_values_by_role():
    base = layout([row("Root", 0), row("Item", 1, ("202", "101"))])
    swapped = replace(
        base,
        columns=tuple(
            replace(c, period_end=base.columns[1 - i].period_end)
            for i, c in enumerate(base.columns)
        ),
    )
    page = parse_layout(swapped, "synthetic.pdf")
    record = list(csv.DictReader(io.StringIO(csv_bytes(page).decode("utf-8-sig"))))[1]
    assert record["previous_year_value"] == "101"
    assert record["current_year_value"] == "202"


def test_parse_page_wrapper_and_committed_examples(parsed):
    fresh = parse_page(PDF)
    assert csv_bytes(fresh) == csv_bytes(parsed)
    assert json_bytes(fresh) == json_bytes(parsed)
    assert (ROOT / "examples/balance_sheet_after_correction_p1.csv").read_bytes() == csv_bytes(
        fresh
    )
    assert (ROOT / "examples/balance_sheet_after_correction_p1.json").read_bytes() == json_bytes(
        fresh
    )


def test_cli_without_encoding_environment(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8=0",
            str(ROOT / "scripts/parse_page.py"),
            str(PDF),
            "--page",
            "1",
            "--out-dir",
            str(tmp_path),
        ],
        env=env,
        cwd=ROOT,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    for suffix in ["csv", "json"]:
        name = f"balance_sheet_after_correction_p1.{suffix}"
        assert (tmp_path / name).read_bytes() == (ROOT / "examples" / name).read_bytes()
