"""Weighted monotone sequence alignment with free gaps and stable earliest-pair ties."""

from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache

from parser.evaluation.data import Table, value_at
from parser.normalize import label_key


@dataclass(frozen=True)
class Alignment:
    pairs: tuple[tuple[int, int], ...]  # prediction index, GT index
    unmatched_prediction: tuple[int, ...]
    unmatched_gt: tuple[int, ...]
    similarities: tuple[float, ...]
    threshold: float


@lru_cache(maxsize=16384)
def _label_similarity(a, b):
    return 1.0 if a == b else SequenceMatcher(None, a, b, autojunk=False).ratio()


def similarity(prediction: Table, gt: Table, i: int, j: int) -> float:
    p, g = prediction.rows[i], gt.rows[j]
    label = _label_similarity(label_key(p.label), label_key(g.label))
    equal = 0
    for role in gt.columns:
        pv, _, valid = value_at(prediction, p, role)
        gv, _, gvalid = value_at(gt, g, role)
        equal += valid and gvalid and pv == gv
    values = equal / len(gt.columns) if gt.columns else 0.0
    return 0.5 * label + 0.5 * values


def align_rows(prediction: Table, gt: Table, threshold: float = 0.5) -> Alignment:
    """Maximize total similarity, then pair count. Ties: match, skip pred, skip GT.

    Suffix DP plus match-first traceback makes otherwise indistinguishable pairs
    choose the earliest current indices. No parent/type evidence influences alignment.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("alignment threshold must be in [0,1]")
    n, m = len(prediction.rows), len(gt.rows)
    scores = [[(0.0, 0) for _ in range(m + 1)] for _ in range(n + 1)]
    actions = [["" for _ in range(m)] for _ in range(n)]
    sims = [[similarity(prediction, gt, i, j) for j in range(m)] for i in range(n)]
    for i in reversed(range(n)):
        for j in reversed(range(m)):
            options = []
            if sims[i][j] >= threshold:
                tail = scores[i + 1][j + 1]
                options.append(((round(sims[i][j] + tail[0], 12), tail[1] + 1), 2, "match"))
            options += [(scores[i + 1][j], 1, "pred"), (scores[i][j + 1], 0, "gt")]
            best = max(options, key=lambda item: (item[0], item[1]))
            scores[i][j], _, actions[i][j] = best
    pairs, matched_sims = [], []
    i = j = 0
    while i < n and j < m:
        action = actions[i][j]
        if action == "match":
            pairs.append((i, j))
            matched_sims.append(sims[i][j])
            i, j = i + 1, j + 1
        elif action == "pred":
            i += 1
        else:
            j += 1
    used_p, used_g = {i for i, _ in pairs}, {j for _, j in pairs}
    return Alignment(
        tuple(pairs),
        tuple(i for i in range(n) if i not in used_p),
        tuple(j for j in range(m) if j not in used_g),
        tuple(matched_sims),
        threshold,
    )
