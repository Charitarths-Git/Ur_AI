"""Render overlapping visual aids for manual P2 transcription; no text extraction."""

from pathlib import Path

from _console import configure_utf8

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "data/derived/crops"
    out.mkdir(parents=True, exist_ok=True)
    bands = [("heading", 50, 147), ("body_1", 145, 302),
             ("body_2", 285, 445), ("body_3", 430, 585), ("body_4", 570, 680)]
    with pymupdf.open(ROOT / "data/raw/balance_sheet_after_correction.pdf") as doc:
        for name, top, bottom in bands:
            pix = doc[0].get_pixmap(dpi=300, clip=pymupdf.Rect(53, top, 526, bottom))
            pix.save(out / f"{name}_300dpi.png")
            print(f"{name}: 300 DPI, clip=(53, {top}, 526, {bottom}) pt")


if __name__ == "__main__":
    configure_utf8()
    main()
