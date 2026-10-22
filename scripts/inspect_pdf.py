#!/usr/bin/env python3
"""
inspect_pdf.py — Diagnostic tool for PDF text-layer inspection.

Phase P1 artifact. This is NOT a parser; it dumps raw extraction data
so that later phases can be designed from evidence.

Usage:
    python scripts/inspect_pdf.py <pdf_path>

Outputs (written to notes/):
    words_pymupdf.json     — every word with bbox, font, size (PyMuPDF)
    words_pdfplumber.json  — every word with bbox (pdfplumber)
    drawings.json          — vector elements (lines, rects)

Also renders page 1 to data/derived/page4_200dpi.png at 200 DPI.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber
import pymupdf
from _console import configure_utf8

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Vertical tolerance for row clustering (in PDF points, 1 pt ≈ 0.35 mm).
# Japanese balance-sheet rows are typically ~10–14 pt tall. A tolerance of
# 3 pt groups tokens whose vertical midpoints are within 3 pt of each other,
# which handles slight baseline shifts between label text and numbers on the
# same visual row without merging adjacent rows.
ROW_CLUSTER_TOLERANCE = 3.0

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTES_DIR = REPO_ROOT / "notes"
DERIVED_DIR = REPO_ROOT / "data" / "derived"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def extract_words_pymupdf(page: pymupdf.Page) -> list[dict]:
    """Extract every word with bbox, font name, and font size using PyMuPDF.

    Uses get_text("dict") to get span-level font information, then splits
    spans into individual words to match word-level granularity.
    """
    words_raw = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)
    # Also get dict-based data for font info
    blocks = page.get_text("dict")["blocks"]

    # Build a lookup: (block_no, line_no, word_no) -> font info
    font_lookup: dict[tuple[int, int], list[dict]] = {}
    for b_idx, block in enumerate(blocks):
        if block["type"] != 0:  # text block
            continue
        for l_idx, line in enumerate(block["lines"]):
            spans = []
            for span in line["spans"]:
                spans.append(
                    {
                        "font": span.get("font", ""),
                        "size": round(span.get("size", 0), 2),
                    }
                )
            font_lookup[(b_idx, l_idx)] = spans

    result = []
    for w in words_raw:
        x0, y0, x1, y1 = round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2)
        text = w[4]
        block_no, line_no = int(w[5]), int(w[6])
        # Try to get font info from the first span of the matching line
        spans = font_lookup.get((block_no, line_no), [])
        font_name = spans[0]["font"] if spans else ""
        font_size = spans[0]["size"] if spans else 0
        result.append(
            {
                "text": text,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "font": font_name,
                "size": font_size,
            }
        )
    return result


def extract_words_pdfplumber(page: pdfplumber.pdf.Page) -> list[dict]:
    """Extract every word with bbox using pdfplumber."""
    words = page.extract_words(keep_blank_chars=True, use_text_flow=False)
    result = []
    for w in words:
        result.append(
            {
                "text": w["text"],
                "x0": round(float(w["x0"]), 2),
                "y0": round(float(w["top"]), 2),  # pdfplumber uses 'top'
                "x1": round(float(w["x1"]), 2),
                "y1": round(float(w["bottom"]), 2),
            }
        )
    return result


def extract_drawings_pymupdf(page: pymupdf.Page) -> list[dict]:
    """Extract vector drawings (lines, rects, curves) from the page."""
    drawings = page.get_drawings()
    result = []
    for d in drawings:
        items_out = []
        for item in d.get("items", []):
            # Each item is a tuple like ("l", p1, p2) for line,
            # ("re", rect) for rectangle, ("c", p1, p2, p3, p4) for curve, etc.
            kind = item[0]
            if kind == "l":
                p1, p2 = item[1], item[2]
                items_out.append(
                    {
                        "type": "line",
                        "x0": round(p1.x, 2),
                        "y0": round(p1.y, 2),
                        "x1": round(p2.x, 2),
                        "y1": round(p2.y, 2),
                    }
                )
            elif kind == "re":
                rect = item[1]
                items_out.append(
                    {
                        "type": "rect",
                        "x0": round(rect.x0, 2),
                        "y0": round(rect.y0, 2),
                        "x1": round(rect.x1, 2),
                        "y1": round(rect.y1, 2),
                    }
                )
            elif kind == "c":
                # Bezier curve — just record the endpoints
                items_out.append(
                    {
                        "type": "curve",
                        "points": [{"x": round(p.x, 2), "y": round(p.y, 2)} for p in item[1:]],
                    }
                )
            elif kind == "qu":
                # Quad — record bounding rect
                quad = item[1]
                items_out.append(
                    {
                        "type": "quad",
                        "rect": {
                            "x0": round(quad.rect.x0, 2),
                            "y0": round(quad.rect.y0, 2),
                            "x1": round(quad.rect.x1, 2),
                            "y1": round(quad.rect.y1, 2),
                        },
                    }
                )
        result.append(
            {
                "fill": str(d.get("fill")),
                "color": str(d.get("color")),
                "width": d.get("width"),
                "items": items_out,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Row clustering
# ---------------------------------------------------------------------------


def cluster_into_rows(words: list[dict], tolerance: float = ROW_CLUSTER_TOLERANCE) -> list[dict]:
    """Group words into visual rows by vertical midpoint.

    Algorithm: sort words by vertical midpoint, then greedily group
    consecutive words whose midpoints are within `tolerance` of the
    running cluster midpoint.

    Returns list of {y_mid, words: [...]} sorted top to bottom.
    """
    if not words:
        return []

    # Compute midpoints
    tagged = []
    for w in words:
        y_mid = (w["y0"] + w["y1"]) / 2
        tagged.append((y_mid, w))
    tagged.sort(key=lambda t: t[0])

    rows: list[dict] = []
    current_mids = [tagged[0][0]]
    current_words = [tagged[0][1]]

    for y_mid, w in tagged[1:]:
        cluster_mid = sum(current_mids) / len(current_mids)
        if abs(y_mid - cluster_mid) <= tolerance:
            current_mids.append(y_mid)
            current_words.append(w)
        else:
            avg_mid = sum(current_mids) / len(current_mids)
            rows.append(
                {
                    "y_mid": round(avg_mid, 2),
                    "words": sorted(current_words, key=lambda ww: ww["x0"]),
                }
            )
            current_mids = [y_mid]
            current_words = [w]

    # Last cluster
    avg_mid = sum(current_mids) / len(current_mids)
    rows.append(
        {
            "y_mid": round(avg_mid, 2),
            "words": sorted(current_words, key=lambda ww: ww["x0"]),
        }
    )

    return rows


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def compute_x_distributions(rows: list[dict]) -> dict:
    """Compute distinct x0 (left-edge) and x1 (right-edge) positions.

    Returns {
        "left_edges": {x0: count},   — label left-edge positions
        "right_edges": {x1: count},  — numeric right-edge positions
    }

    We round to nearest integer to group minor sub-pixel differences.
    """
    left_counts: dict[int, int] = defaultdict(int)
    right_counts: dict[int, int] = defaultdict(int)

    for row in rows:
        if not row["words"]:
            continue
        # First word in row is typically the label
        first_x0 = round(row["words"][0]["x0"])
        left_counts[first_x0] += 1
        # Right edges of all words (useful for numeric column detection)
        for w in row["words"]:
            right_x1 = round(w["x1"])
            right_counts[right_x1] += 1

    return {
        "left_edges": dict(sorted(left_counts.items())),
        "right_edges": dict(sorted(right_counts.items())),
    }


# ---------------------------------------------------------------------------
# Page metadata
# ---------------------------------------------------------------------------


def get_page_metadata(pdf_path: str | Path) -> dict:
    """Report page count, size, rotation, and image presence."""
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(pdf_path)
    meta = {"page_count": len(doc), "pages": []}
    for i, page in enumerate(doc):
        images = page.get_images(full=True)
        meta["pages"].append(
            {
                "page_number": i + 1,
                "width": round(page.rect.width, 2),
                "height": round(page.rect.height, 2),
                "rotation": page.rotation,
                "image_count": len(images),
            }
        )
    doc.close()
    return meta


# ---------------------------------------------------------------------------
# PNG rendering
# ---------------------------------------------------------------------------


def render_page_to_png(pdf_path: str | Path, page_index: int = 0, dpi: int = 200) -> Path:
    """Render a page to PNG. Returns the output path."""
    pdf_path = Path(pdf_path)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "page4_200dpi.png"

    doc = pymupdf.open(pdf_path)
    page = doc[page_index]
    # Scale factor: default resolution is 72 DPI
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    pix.save(str(out_path))
    doc.close()
    return out_path


# ---------------------------------------------------------------------------
# Main inspection function
# ---------------------------------------------------------------------------


def run_inspection(pdf_path: str | Path) -> dict:
    """Run the full inspection pipeline. Returns a summary dict.

    Side effects: writes JSON files to notes/ and PNG to data/derived/.
    """
    pdf_path = Path(pdf_path)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Page metadata ----
    meta = get_page_metadata(pdf_path)
    print("=" * 60)
    print("PAGE METADATA")
    print("=" * 60)
    for p in meta["pages"]:
        print(
            f"  Page {p['page_number']}: {p['width']}x{p['height']} pt, "
            f"rotation={p['rotation']}°, images={p['image_count']}"
        )
    print()

    # ---- PyMuPDF word extraction (page 1) ----
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    words_mu = extract_words_pymupdf(page)
    doc.close()

    words_mu_path = NOTES_DIR / "words_pymupdf.json"
    with open(words_mu_path, "w", encoding="utf-8") as f:
        json.dump(words_mu, f, ensure_ascii=False, indent=2)
    print(f"PyMuPDF: {len(words_mu)} words → {words_mu_path.name}")

    # ---- pdfplumber word extraction (page 1) ----
    with pdfplumber.open(pdf_path) as pdf:
        ppage = pdf.pages[0]
        words_pb = extract_words_pdfplumber(ppage)

    words_pb_path = NOTES_DIR / "words_pdfplumber.json"
    with open(words_pb_path, "w", encoding="utf-8") as f:
        json.dump(words_pb, f, ensure_ascii=False, indent=2)
    print(f"pdfplumber: {len(words_pb)} words → {words_pb_path.name}")
    print()

    # ---- Vector drawings (page 1) ----
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    drawings = extract_drawings_pymupdf(page)
    doc.close()

    drawings_path = NOTES_DIR / "drawings.json"
    with open(drawings_path, "w", encoding="utf-8") as f:
        json.dump(drawings, f, ensure_ascii=False, indent=2)

    line_count = sum(1 for d in drawings for item in d["items"] if item["type"] == "line")
    rect_count = sum(1 for d in drawings for item in d["items"] if item["type"] == "rect")
    print(
        f"Drawings: {len(drawings)} draw commands, "
        f"{line_count} lines, {rect_count} rects → {drawings_path.name}"
    )
    print()

    # ---- Row clustering (using PyMuPDF words) ----
    rows = cluster_into_rows(words_mu)
    print("=" * 60)
    print(f"ROW CLUSTERING (tolerance={ROW_CLUSTER_TOLERANCE} pt, using PyMuPDF words)")
    print("=" * 60)
    for i, row in enumerate(rows):
        first_x0 = row["words"][0]["x0"] if row["words"] else 0
        text = " | ".join(w["text"] for w in row["words"])
        print(f"  Row {i + 1:3d}  y={row['y_mid']:7.2f}  x0={first_x0:7.2f}  {text}")
    print()

    # ---- x0 / x1 distributions ----
    x_dist = compute_x_distributions(rows)
    print("=" * 60)
    print("LEFT-EDGE (x0) DISTRIBUTION (rounded to nearest int)")
    print("=" * 60)
    for x0, count in x_dist["left_edges"].items():
        print(f"  x0={x0:4d}  count={count}")
    print()

    print("=" * 60)
    print("RIGHT-EDGE (x1) DISTRIBUTION (rounded to nearest int)")
    print("=" * 60)
    for x1, count in sorted(x_dist["right_edges"].items()):
        if count >= 2:  # Only show positions used by 2+ words (reduce noise)
            print(f"  x1={x1:4d}  count={count}")
    print()

    # ---- Render page to PNG ----
    png_path = render_page_to_png(pdf_path, page_index=0, dpi=200)
    print(f"Rendered page 1 at 200 DPI → {png_path}")

    return {
        "metadata": meta,
        "words_pymupdf_count": len(words_mu),
        "words_pdfplumber_count": len(words_pb),
        "drawing_count": len(drawings),
        "line_count": line_count,
        "rect_count": rect_count,
        "row_count": len(rows),
        "x_distributions": x_dist,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    configure_utf8()
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <pdf_path>")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    if not pdf_file.exists():
        print(f"Error: file not found: {pdf_file}")
        sys.exit(1)

    summary = run_inspection(pdf_file)
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Pages: {summary['metadata']['page_count']}")
    print(f"  PyMuPDF words: {summary['words_pymupdf_count']}")
    print(f"  pdfplumber words: {summary['words_pdfplumber_count']}")
    print(
        f"  Drawings: {summary['drawing_count']} "
        f"(lines={summary['line_count']}, rects={summary['rect_count']})"
    )
    print(f"  Visual rows: {summary['row_count']}")
