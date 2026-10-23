"""Regression coverage for structural headings and independent JSON evaluation."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from test_rows import body, synthetic_page, word

from parser.evaluation.report import evaluate_files
from parser.export import csv_bytes, json_bytes, parse_layout, parse_page
from parser.layout_types import Word
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/balance_sheet_after_correction.pdf"
CSV = ROOT / "examples/balance_sheet_after_correction_p1.csv"
JSON = CSV.with_suffix(".json")
GT = ROOT / "data/gt/page4.csv"


def test_footer_date_cannot_erase_table():
    raw = read_pdf_page(PDF)
    changed = replace(
        raw,
        words=raw.words
        + (Word("Updated 2026年10月23日", 20, raw.height - 20, 180, raw.height - 10),),
    )
    page = parse_layout(reconstruct_page(changed), PDF.name)
    original = parse_page(PDF)
    assert csv_bytes(page) == csv_bytes(original)
    assert json_bytes(page) == json_bytes(original)


def test_date_in_body_label_does_not_redefine_header():
    page = synthetic_page()
    words = tuple(
        replace(w, text="2026年10月23日取得資産") if w.text == "Second" else w for w in page.words
    )
    rows = body(reconstruct_page(replace(page, words=words)))
    assert len(rows) == 5
    assert rows[2].label == "2026年10月23日取得資産"
    assert len(rows[2].cells) == 2


def test_genuine_period_band_keeps_header_only_section():
    layout = reconstruct_page(synthetic_page())
    assert body(layout)[0].label == "Section"
    assert [c.period_end for c in layout.columns] == [(2025, 3, 31), (2026, 3, 31)]


@pytest.mark.parametrize("ambiguous", [False, True])
def test_missing_or_ambiguous_dates_warn_and_fallback(ambiguous):
    page = synthetic_page()
    words = list(page.words)
    if ambiguous:
        words.append(word("2024年3月31日", 120, 55, 72))
    else:
        words = [w for w in words if "年" not in w.text]
    layout = reconstruct_page(replace(page, words=words))
    assert body(layout)[0].label == "Series 2 item"
    assert any(w.code.startswith("header_dates_") for w in layout.warnings)


def nodes(document):
    pending = list(document["rows"])
    while pending:
        n = pending.pop(0)
        yield n
        pending[0:0] = n["children"]


@pytest.mark.parametrize(
    "fault",
    [
        "empty",
        "drop",
        "nesting",
        "duplicate",
        "value",
        "children",
        "malformed",
        "level",
        "missing_id",
    ],
)
def test_json_faults_do_not_borrow_perfect_csv_scores(tmp_path, fault):
    doc = json.loads(JSON.read_text(encoding="utf-8"))
    all_nodes = list(nodes(doc))
    if fault == "empty":
        doc["rows"] = []
    elif fault == "drop":
        all_nodes[-2]["children"] = []
        doc["rows"].pop()
    elif fault == "nesting":
        child = doc["rows"][0]["children"].pop(0)
        child["level"] = 0
        doc["rows"].append(child)
    elif fault == "duplicate":
        doc["rows"].append(copy.deepcopy(doc["rows"][0]))
    elif fault == "value":
        n = next(n for n in all_nodes if n["values"]["previous_year"]["value"] is not None)
        n["values"]["previous_year"]["value"] += 100
    elif fault == "children":
        all_nodes[0]["children"] = {}
    elif fault == "level":
        all_nodes[-1]["level"] += 1
    elif fault == "missing_id":
        del all_nodes[-1]["row_id"]
    path = tmp_path / "bad.json"
    path.write_text("{" if fault == "malformed" else json.dumps(doc), encoding="utf-8")
    result = evaluate_files(CSV, GT, path)
    assert result["metrics"]["fully_correct_rows"]["numerator"] == 43
    assert result["json_validation"]["passes"] is False
    assert result["validation_passes"] is False
    if fault == "empty":
        assert (
            result["json_validation"]["gt_accuracy"]["metrics"]["fully_correct_rows"]["numerator"]
            == 0
        )


def test_correct_json_and_optional_omission_distinguished():
    report = evaluate_files(CSV, GT, JSON)
    assert report["json_validation"]["passes"]
    assert (
        report["json_validation"]["gt_accuracy"]["metrics"]["fully_correct_rows"]["numerator"] == 43
    )
    assert evaluate_files(CSV, GT)["json_validation"]["status"] == "not_supplied"
