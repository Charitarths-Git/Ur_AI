"""The package's only PyMuPDF dependency; adapter for born-digital unrotated PDFs."""

from pathlib import Path
from statistics import median
from typing import Protocol

import pymupdf

from parser.layout_types import LayoutConfig, RawPage, Rule, Word


class PageBackend(Protocol):
    """Replaceable extraction boundary; an OCR/VLM adapter can implement it later."""

    def read_page(
        self, path: str | Path, page_number: int = 1, config: LayoutConfig = LayoutConfig()
    ) -> RawPage: ...


class PyMuPDFBackend:
    def read_page(
        self, path: str | Path, page_number: int = 1, config: LayoutConfig = LayoutConfig()
    ) -> RawPage:
        with pymupdf.open(path) as document:
            if not 1 <= page_number <= len(document):
                raise ValueError("page_number is one-based and must exist in the PDF")
            page = document[page_number - 1]
            if page.rotation:
                raise ValueError("rotated pages are unsupported by this backend")
            spans = [
                span
                for block in page.get_text("dict")["blocks"]
                if block["type"] == 0
                for line in block["lines"]
                for span in line["spans"]
            ]
            words = []
            for x0, y0, x1, y1, text, *_ in page.get_text("words"):
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                size = next(
                    (
                        span["size"]
                        for span in spans
                        if span["bbox"][0] <= cx <= span["bbox"][2]
                        and span["bbox"][1] <= cy <= span["bbox"][3]
                    ),
                    None,
                )
                words.append(Word(text, x0, y0, x1, y1, size))
            heights = [w.y1 - w.y0 for w in words if w.y1 > w.y0]
            h = median(heights) if heights else page.rect.height * config.fallback_height_fraction
            rules = []
            for drawing in page.get_drawings():
                for item in drawing["items"]:
                    if item[0] == "re":
                        rect = item[1]
                        x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                        height = y1 - y0
                    elif item[0] == "l":
                        p, q = item[1:3]
                        x0, x1 = sorted((p.x, q.x))
                        y0, y1 = sorted((p.y, q.y))
                        height = max(y1 - y0, drawing.get("width") or 0)
                    else:
                        continue
                    if (
                        height <= h * config.rule_max_height
                        and x1 - x0 >= h * config.rule_min_width
                    ):
                        rules.append(Rule(x0, y0, x1, y1, height))
            return RawPage(page.rect.width, page.rect.height, words, rules)


def read_pdf_page(
    path: str | Path, page_number: int = 1, config: LayoutConfig = LayoutConfig()
) -> RawPage:
    """Read a one-based PDF page through the default backend; no reconstruction."""
    return PyMuPDFBackend().read_page(path, page_number, config)
