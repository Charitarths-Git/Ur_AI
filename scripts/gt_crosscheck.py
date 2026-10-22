"""Read-only P2 text-layer diagnostic, authored AFTER image GT commit 7ca2ef8.

Page-specific coordinates and token handling are throwaway verification aids,
not parsing/normalization/evaluation code for the package. Never rewrites GT.
"""

import csv
import hashlib
import re
from pathlib import Path

import pymupdf
from _console import configure_utf8

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"(?:△?[0-9]+(?:,[0-9]{3})*|－)\Z")


def token_value(raw):
    """Only the literal forms on this page; no general normalization utility."""
    if raw == "－":
        return None
    return int(raw.replace("△", "-").replace(",", ""))


def main():
    gt = ROOT / "data/gt/page4.csv"
    before = hashlib.sha256(gt.read_bytes()).hexdigest()
    with gt.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["row_type"] != "header"]
    # Crop bounds match the visually reviewed table body, excluding dates/footer.
    with pymupdf.open(ROOT / "data/raw/balance_sheet_after_correction.pdf") as doc:
        words = doc[0].get_text("words", clip=pymupdf.Rect(54, 146, 526, 678))
    disagreements = []
    print("Read-only text cross-check; image GT committed first in 7ca2ef8.")
    print("Rows aligned in vertical reading order independently within each value column.")
    print("Only numeric/nil tokens inside the body are considered; dates/footer excluded.")
    checked = 0
    for name, value_col, raw_col, left, right in [
        ("previous", "previous_year_value", "prev_raw", 390, 402),
        ("current", "current_year_value", "curr_raw", 518, 528),
    ]:
        tokens = sorted(
            [w for w in words if left <= w[2] <= right and TOKEN.fullmatch(w[4])],
            key=lambda w: (w[1], w[0]),
        )
        print(f"{name}: GT cells={len(rows)}, text numeric/nil tokens={len(tokens)}")
        if len(tokens) != len(rows):
            disagreements.append(
                f"{name}: token count mismatch; ordinal alignment may be unreliable"
            )
        for index, row in enumerate(rows):
            if index >= len(tokens):
                disagreements.append(f"{row['row_id']} {name}: missing text token")
                continue
            word = tokens[index]
            raw = word[4]
            value = int(row[value_col]) if row[value_col] != "" else None
            if value != token_value(raw) or row[raw_col] != raw:
                disagreements.append(
                    f"{row['row_id']} {row['label']} {name}: "
                    f"GT={row[raw_col]!r} ({value}), text={raw!r} ({token_value(raw)}), "
                    f"y0={word[1]:.2f}"
                )
            checked += 1
        for word in tokens[len(rows) :]:
            disagreements.append(f"{name}: extra text token {word[4]!r} at y0={word[1]:.2f}")
    print(f"Compared cells: {checked} (including nil marks and signed zero).")
    print(f"Disagreements: {len(disagreements)}")
    for disagreement in disagreements:
        print("  " + disagreement)
    after = hashlib.sha256(gt.read_bytes()).hexdigest()
    if after != before:
        raise RuntimeError("Ground truth changed during this read-only diagnostic")
    print(f"GT SHA-256 unchanged: {after}")
    print("Human adjudication against the rendered image remains required.")


if __name__ == "__main__":
    configure_utf8()
    main()
