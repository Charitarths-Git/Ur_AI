"""Smoke tests — verify the PDF is present and readable."""

from pathlib import Path

import pymupdf


PDF_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "balance_sheet_after_correction.pdf"


def test_pdf_exists():
    """The source PDF must be present in data/raw/."""
    assert PDF_PATH.exists(), f"PDF not found at {PDF_PATH}"


def test_pdf_has_pages():
    """The PDF must have at least one page."""
    doc = pymupdf.open(PDF_PATH)
    assert len(doc) >= 1, "PDF has no pages"
    doc.close()


def test_pdf_has_text_layer():
    """The first page must contain extractable text (born-digital check)."""
    doc = pymupdf.open(PDF_PATH)
    page = doc[0]
    text = page.get_text()
    doc.close()
    assert len(text.strip()) > 0, "First page has no extractable text"
