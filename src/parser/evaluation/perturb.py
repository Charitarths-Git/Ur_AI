"""Deterministic RawPage perturbations, moved from the existing P4/P5 test helpers."""

import random
from dataclasses import replace

from parser.layout_types import RawPage
from parser.rows import reconstruct_page


def transform(page: RawPage, mode: str, seed: int = 813, amplitude: float = 0.015) -> RawPage:
    rng = random.Random(seed)
    scale, dx, dy = 1, 0, 0
    if mode == "translate":
        dx, dy = -240, 375
    elif mode == "scale_small":
        scale = 0.45
    elif mode == "scale_large":
        scale = 2.75
    elif mode == "combined":
        scale, dx, dy = 1.7, 220, -400
    elif mode not in {"shuffle", "jitter", "jitter_x", "jitter_y"}:
        raise ValueError(f"unknown perturbation: {mode}")
    if amplitude < 0:
        raise ValueError("jitter amplitude must be nonnegative")
    h = reconstruct_page(page).thresholds.median_word_height
    words = []
    for word in page.words:
        jx = jy = 0
        if mode.startswith("jitter"):
            jx, jy = (rng.uniform(-amplitude, amplitude) * h for _ in range(2))
            if mode == "jitter_x":
                jy = 0
            elif mode == "jitter_y":
                jx = 0
        words.append(replace(word, x0=word.x0 * scale + dx + jx, x1=word.x1 * scale + dx + jx,
                             y0=word.y0 * scale + dy + jy, y1=word.y1 * scale + dy + jy,
                             size=word.size * scale if word.size is not None else None))
    rules = [replace(r, x0=r.x0 * scale + dx, x1=r.x1 * scale + dx,
                     y0=r.y0 * scale + dy, y1=r.y1 * scale + dy, height=r.height * scale)
             for r in page.rules]
    if mode in {"shuffle", "combined", "jitter", "jitter_x", "jitter_y"}:
        rng.shuffle(words)
        rng.shuffle(rules)
    return RawPage(page.width * scale, page.height * scale, words, rules)


def flatten_indentation(raw: RawPage) -> RawPage:
    page = reconstruct_page(raw)
    labels = [r for r in page.rows if r.zone == "body" and r.label_x0 is not None]
    if not labels:
        return raw
    common = min(r.label_x0 for r in labels)
    replacements = {}
    for row in labels:
        shift = common - row.label_x0
        for word in row.source_words:
            if not any(abs(word.x1 - c.x1_centre) <= page.thresholds.column_tolerance for c in page.columns):
                replacements[word] = replace(word, x0=word.x0 + shift, x1=word.x1 + shift)
    return replace(raw, words=tuple(replacements.get(word, word) for word in raw.words))


def drop_rules(raw: RawPage) -> RawPage:
    return replace(raw, rules=())
