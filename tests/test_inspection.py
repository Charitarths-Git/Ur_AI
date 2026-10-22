"""Tests for the PDF inspection script (scripts/inspect_pdf.py).

P1 requirement: assert that expected output files are produced and non-empty.
Do NOT assert any financial values or label counts.
"""

import json

# Bring the scripts directory onto sys.path so we can import inspect_pdf
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import inspect_pdf  # noqa: E402

PDF_PATH = REPO_ROOT / "data" / "raw" / "balance_sheet_after_correction.pdf"
NOTES_DIR = REPO_ROOT / "notes"
DERIVED_DIR = REPO_ROOT / "data" / "derived"


@pytest.fixture(scope="module")
def inspection_summary():
    """Run the full inspection pipeline once; return the summary dict."""
    return inspect_pdf.run_inspection(PDF_PATH)


def test_inspection_words_pymupdf_json_exists_and_nonempty(inspection_summary):
    """words_pymupdf.json must be written and contain at least one word."""
    path = NOTES_DIR / "words_pymupdf.json"
    assert path.exists(), f"words_pymupdf.json not found at {path}"
    assert path.stat().st_size > 0, "words_pymupdf.json is empty"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "words_pymupdf.json must be a JSON array"
    assert len(data) > 0, "words_pymupdf.json contains no words"


def test_inspection_words_pdfplumber_json_exists_and_nonempty(inspection_summary):
    """words_pdfplumber.json must be written and contain at least one word."""
    path = NOTES_DIR / "words_pdfplumber.json"
    assert path.exists(), f"words_pdfplumber.json not found at {path}"
    assert path.stat().st_size > 0, "words_pdfplumber.json is empty"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "words_pdfplumber.json must be a JSON array"
    assert len(data) > 0, "words_pdfplumber.json contains no words"


def test_inspection_drawings_json_exists_and_nonempty(inspection_summary):
    """drawings.json must be written (even if drawings list is empty)."""
    path = NOTES_DIR / "drawings.json"
    assert path.exists(), f"drawings.json not found at {path}"
    assert path.stat().st_size > 0, "drawings.json is empty"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "drawings.json must be a JSON array"


def test_inspection_png_exists_and_nonempty(inspection_summary):
    """page4_200dpi.png must be rendered and non-empty."""
    path = DERIVED_DIR / "page4_200dpi.png"
    assert path.exists(), f"page4_200dpi.png not found at {path}"
    assert path.stat().st_size > 10_000, (
        f"page4_200dpi.png is too small ({path.stat().st_size} bytes) — likely a failed render"
    )


def test_inspection_summary_structure(inspection_summary):
    """The summary dict must have the expected top-level keys."""
    required_keys = {
        "metadata",
        "words_pymupdf_count",
        "words_pdfplumber_count",
        "drawing_count",
        "row_count",
    }
    missing = required_keys - inspection_summary.keys()
    assert not missing, f"Summary dict missing keys: {missing}"


def test_inspection_page_metadata(inspection_summary):
    """The PDF must report at least one page with positive dimensions."""
    meta = inspection_summary["metadata"]
    assert meta["page_count"] >= 1, "PDF must have at least one page"
    for page in meta["pages"]:
        assert page["width"] > 0, "Page width must be positive"
        assert page["height"] > 0, "Page height must be positive"


def test_inspection_row_clustering_produces_rows(inspection_summary):
    """Row clustering must produce at least one row."""
    assert inspection_summary["row_count"] > 0, (
        "Row clustering produced zero rows — likely a failure in extraction"
    )


def test_each_word_has_required_fields(inspection_summary):
    """Every word in words_pymupdf.json must have x0, y0, x1, y1, and text."""
    path = NOTES_DIR / "words_pymupdf.json"
    with open(path, encoding="utf-8") as f:
        words = json.load(f)
    required = {"x0", "y0", "x1", "y1", "text"}
    for i, w in enumerate(words):
        missing = required - w.keys()
        assert not missing, f"Word {i} missing fields {missing}: {w}"
