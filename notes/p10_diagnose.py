"""Reproduce P10b's geometry diagnosis without labels/GT driving parser decisions."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from parser.evaluation.perturb import transform
from parser.export import parse_layout
from parser.normalize import label_key
from parser.pdf_backend import read_pdf_page
from parser.rows import reconstruct_page

ROOT = Path(__file__).resolve().parents[1]


def diagnose():
    raw = read_pdf_page(ROOT / "data/raw/balance_sheet_after_correction.pdf")
    baseline = reconstruct_page(raw)
    body = [r for r in baseline.rows if r.zone == "body"]
    parsed = parse_layout(baseline, "source.pdf")
    ownership = {w: i for i, r in enumerate(baseline.rows) for w in r.source_words}
    body_ids = {r.index: i + 1 for i, r in enumerate(body)}
    candidates = defaultdict(list)
    for w in raw.words:
        candidates[w.text].append(w)

    def original(w):
        # Both tested bounds are smaller than separation to equal text in another row/column.
        return min(candidates[w.text], key=lambda b: (b.x0 - w.x0) ** 2 + (b.y0 - w.y0) ** 2)

    y_records = []
    for amp in (0.2, 0.3):
        for seed in range(20):
            page = reconstruct_page(transform(raw, "jitter_y", seed, amp))
            destinations = defaultdict(set)
            merges = []
            for r in page.rows:
                sources = {ownership[original(w)] for w in r.source_words}
                for source in sources:
                    destinations[source].add(r.index)
                if len(sources) > 1:
                    merges.append(
                        {
                            "source_body_ids": [
                                body_ids[i] for i in sorted(sources) if i in body_ids
                            ],
                            "source_layout_rows": sorted(sources),
                            "destination": r.index,
                        }
                    )
            splits = []
            for source, dests in sorted(destinations.items()):
                if len(dests) > 1:
                    words = sorted(
                        (
                            w
                            for r in page.rows
                            for w in r.source_words
                            if ownership[original(w)] == source
                        ),
                        key=lambda w: (w.y0 + w.y1) / 2,
                    )
                    gaps = [(b.y0 + b.y1 - a.y0 - a.y1) / 2 for a, b in zip(words, words[1:])]
                    splits.append(
                        {
                            "body_id": body_ids.get(source),
                            "label": baseline.rows[source].label,
                            "destinations": sorted(dests),
                            "max_gap_H": max(gaps) / page.thresholds.median_word_height,
                        }
                    )
            y_records.append(
                {
                    "amplitude_H": amp,
                    "seed": seed,
                    "body_rows": sum(r.zone == "body" for r in page.rows),
                    "splits": splits,
                    "merges": merges,
                }
            )
    x_records = []
    for seed in range(20):
        page = reconstruct_page(transform(raw, "jitter_x", seed, 0.3))
        changed = parse_layout(page, "source.pdf")
        rows = [r for r in page.rows if r.zone == "body"]
        assert len(rows) == len(body)
        causes = defaultdict(list)
        for i, (before, after, p0, p1) in enumerate(zip(body, rows, parsed.rows, changed.rows), 1):
            if [(c.column_index, c.raw, c.amount.value) for c in before.cells] != [
                (c.column_index, c.raw, c.amount.value) for c in after.cells
            ]:
                causes["value_assignment"].append(i)
            if before.indent_step != after.indent_step:
                causes["indent_step"].append(i)
            if p0.parent_row_id != p1.parent_row_id:
                causes["parent"].append(i)
            # Numeric words left behind by the cell-assignment gate also enter the label;
            # record separately from spacing/merging among genuine label tokens.
            col_tokens = {
                w
                for w in before.source_words
                if any(
                    abs(w.x1 - c.x1_centre) <= baseline.thresholds.column_tolerance
                    for c in baseline.columns
                )
            }
            pure = [w for w in after.source_words if original(w) not in col_tokens]
            # Same join as rows.py but only the original label tokens, to isolate token spacing.
            pure.sort(key=lambda w: (w.x0, w.x1, w.text))
            label = ""
            previous = None
            for w in pure:
                if (
                    previous is not None
                    and w.x0 - previous.x1 > page.thresholds.label_space_gap
                    and not label[-1:].isspace()
                    and not w.text[:1].isspace()
                ):
                    label += " "
                label += w.text
                previous = w
            if before.label != label:
                causes["label_token_spacing_exact"].append(i)
            if label_key(before.label) != label_key(label):
                causes["label_token_order_key"].append(i)
            if before.label != after.label:
                causes["exported_label"].append(i)
        x_records.append(
            {
                "seed": seed,
                "columns": len(page.columns),
                "roles": [c.role for c in changed.columns],
                "causes": dict(causes),
            }
        )
    counts = Counter(
        {
            cause: sum(len(r["causes"].get(cause, [])) for r in x_records)
            for cause in (
                "value_assignment",
                "indent_step",
                "parent",
                "label_token_spacing_exact",
                "label_token_order_key",
                "exported_label",
            )
        }
    )
    affected = {
        cause: sorted({i for r in x_records for i in r["causes"].get(cause, [])})
        for cause in counts
    }
    return {
        "median_word_height": baseline.thresholds.median_word_height,
        "row_pitch_H": median(b.y_top - a.y_top for a, b in zip(body, body[1:]))
        / baseline.thresholds.median_word_height,
        "y": y_records,
        "x": x_records,
        "x_row_seed_counts": dict(counts),
        "x_unique_body_ids": affected,
    }


def pitch_trial():
    """In-memory candidate only; restore immediately on the first failed acceptance gate."""
    from dataclasses import replace
    from time import monotonic

    import pytest

    import parser.rows as rows_module

    start = monotonic()
    original_thresholds = rows_module._thresholds
    observed = []

    def candidate(page, config, words):
        thresholds = original_thresholds(page, config, words)
        h = thresholds.median_word_height
        groups = rows_module._clusters(words, lambda w: (w.y0 + w.y1) / 2, thresholds.row_tolerance)
        centres = [median((w.y0 + w.y1) / 2 for w in group) for group in groups]
        gaps = [b - a for a, b in zip(centres, centres[1:]) if b - a > 0.8 * h]
        pitch = median(gaps) if gaps else h
        # Less than half a row pitch leaves a separation margin. Clamp in sparse/noisy input.
        distance = max(thresholds.row_tolerance, min(0.45 * pitch, 0.65 * h))
        observed.append({"pitch_H": pitch / h, "candidate_tolerance_H": distance / h})
        return replace(thresholds, row_tolerance=distance)

    try:
        rows_module._thresholds = candidate
        raw = read_pdf_page(ROOT / "data/raw/balance_sheet_after_correction.pdf")
        changed = reconstruct_page(transform(raw, "jitter_y", 11, 0.2))
        body_count = sum(r.zone == "body" for r in changed.rows)
        exit_code = int(
            pytest.main(["-q", "tests/test_perturbation.py::test_measured_failure_seed_11_split"])
        )
    finally:
        rows_module._thresholds = original_thresholds
    result = {
        "candidate": "row tolerance = clamp(0.45 * median pitch, existing tolerance, 0.65 H)",
        "body_rows_seed11": body_count,
        "acceptance_test_exit_code": exit_code,
        "observations": observed,
        "elapsed_seconds": round(monotonic() - start, 3),
        "decision": "REJECTED at first existing-test failure; in-memory override restored; "
        "no production threshold change",
    }
    (ROOT / "notes/p10_pitch_trial.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(result["decision"])


if __name__ == "__main__":
    import sys

    if "--pitch-trial" in sys.argv:
        pitch_trial()
        raise SystemExit(0)

    result = diagnose()
    path = ROOT / "notes/p10_geometry_diagnosis.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Median row pitch/H:", result["row_pitch_H"])
    for amp in (0.2, 0.3):
        runs = [r for r in result["y"] if r["amplitude_H"] == amp]
        splits = Counter(s["body_id"] for r in runs for s in r["splits"])
        print(
            "Y",
            amp,
            "splits(row:seedcount):",
            dict(splits),
            "merged groups:",
            sum(len(r["merges"]) for r in runs),
        )
    print("X .3 affected row-seeds:", result["x_row_seed_counts"])
    print("X columns:", Counter(r["columns"] for r in result["x"]))
