"""Pure visual reconstruction from backend-neutral words and rules.

No document-specific coordinates, accounting vocabulary, GT access or semantic
hierarchy. See LayoutConfig for relative thresholds and notes/row_reconstruction.md
for heuristics and their limitations. Row/column/indent indices are zero-based.
"""

from dataclasses import replace
from statistics import median

from parser.layout_types import (
    Cell,
    Column,
    LayoutConfig,
    LayoutThresholds,
    PageLayout,
    ParseWarning,
    RawPage,
    Row,
)
from parser.normalize import label_key, parse_amount, parse_period_end

_SIGNS = frozenset("△▲－―—–−‐ー-")


def _thresholds(page, config, words):
    heights = [w.y1 - w.y0 for w in words if w.y1 > w.y0]
    h = median(heights) if heights else page.height * config.fallback_height_fraction
    distances = {
        name: getattr(config, name) * h
        for name in (
            "row_tolerance",
            "column_tolerance",
            "label_space_gap",
            "sign_gap",
            "indent_tolerance",
            "rule_max_height",
            "rule_min_width",
            "rule_vertical_tolerance",
            "single_column_heading_pad",
        )
    }
    return LayoutThresholds(h, **distances, column_min_support=config.column_min_support)


def _clusters(items, position, tolerance):
    """Sorted 1D groups using gap-based clustering when gap exceeds tolerance."""
    groups = []
    for item in sorted(items, key=position):
        if not groups or position(item) - position(groups[-1][-1]) > tolerance:
            groups.append([item])
        else:
            groups[-1].append(item)
    return groups


def _join_words(words, space_gap):
    text = ""
    previous = None
    for word in words:
        if (
            previous is not None
            and word.x0 - previous.x1 > space_gap
            and not text[-1:].isspace()
            and not word.text[:1].isspace()
        ):
            text += " "
        text += word.text
        previous = word
    return text


def _token_groups(words, thresholds):
    """Keep original words; only a cell's raw text concatenates a split sign."""
    groups = []
    i = 0
    while i < len(words):
        word = words[i]
        if word.text in _SIGNS and i + 1 < len(words):
            following = words[i + 1]
            parsed = parse_amount(following.text)
            gap = following.x0 - word.x1
            if (
                parsed.status == "ok"
                and not parsed.negative
                and -thresholds.column_tolerance <= gap <= thresholds.sign_gap
            ):
                groups.append((word, following))
                i += 2
                continue
        groups.append((word,))
        i += 1
    return groups


def _column_centres(token_rows, thresholds):
    candidates = []
    for row_index, tokens in enumerate(token_rows):
        for token in tokens:
            raw = "".join(w.text for w in token)
            if parse_amount(raw).status in {"ok", "nil"}:
                candidates.append((token[-1].x1, row_index))
    clusters = _clusters(candidates, lambda x: x[0], thresholds.column_tolerance)
    return tuple(
        median(x[0] for x in group)
        for group in clusters
        if len({x[1] for x in group}) >= thresholds.column_min_support
    )


def _cells(tokens, centres, thresholds):
    assigned = {}
    used = set()
    for token in tokens:
        if not centres:
            continue
        column = min(range(len(centres)), key=lambda i: abs(token[-1].x1 - centres[i]))
        if abs(token[-1].x1 - centres[column]) <= thresholds.column_tolerance:
            assigned.setdefault(column, []).extend(token)
            used.update(token)
    cells = []
    for column, words in sorted(assigned.items()):
        # Multiple aligned fragments in one cell are kept, not silently discarded.
        # _token_groups handles the special no-space sign+digits case first.
        matching_tokens = [t for t in tokens if any(w in words for w in t)]
        raw = " ".join("".join(w.text for w in t) for t in matching_tokens)
        cells.append(Cell(column, raw, parse_amount(raw)))
    return tuple(cells), used


def _columns(centres, row_words, header_end, token_rows, thresholds):
    columns = []
    for index, centre in enumerate(centres):
        if index:
            left = centres[index - 1]
        elif len(centres) > 1:
            left = centre - (centres[1] - centre)
        else:
            starts = [
                t[0].x0
                for tokens in token_rows
                for t in tokens
                if abs(t[-1].x1 - centre) <= thresholds.column_tolerance
            ]
            left = min(starts, default=centre) - thresholds.single_column_heading_pad
        lines = []
        for words in row_words[: header_end + 1]:
            above = [
                w for w in words if left < (w.x0 + w.x1) / 2 <= centre + thresholds.column_tolerance
            ]
            if above:
                lines.append(_join_words(above, thresholds.label_space_gap))
        heading = "\n".join(lines)
        columns.append(Column(index, centre, heading, parse_period_end(heading)))
    return tuple(columns)


def _has_rule(page, previous_bottom, row_top, value_spans, thresholds):
    if previous_bottom is None:
        return False
    slack = thresholds.rule_vertical_tolerance
    for rule in page.rules:
        if (
            rule.height <= thresholds.rule_max_height
            and rule.x1 - rule.x0 >= thresholds.rule_min_width
            and rule.y0 >= previous_bottom - slack
            and rule.y1 <= row_top + slack
            and any(
                rule.x1 >= left - thresholds.column_tolerance
                and rule.x0 <= right + thresholds.column_tolerance
                for left, right in value_spans
            )
        ):
            return True
    return False


def reconstruct_page(raw_page: RawPage, config: LayoutConfig = LayoutConfig()) -> PageLayout:
    """Reconstruct visual rows using relative geometry only; never mutate input.

    Last complete date row ends the header. Without dates, the first supported
    valid value row begins the body (preceding label-only rows stay header).
    All rows after the last aligned cell are footer; without supported values,
    all nonempty rows are header. Blank words/zero-height boxes are ignored.
    """
    words = [w for w in raw_page.words if label_key(w.text) and w.y1 > w.y0]
    thresholds = _thresholds(raw_page, config, words)
    # Tie-breakers make grouping independent of backend/stream order.
    words.sort(key=lambda w: ((w.y0 + w.y1) / 2, w.x0, w.x1, w.text))
    groups = _clusters(words, lambda w: (w.y0 + w.y1) / 2, thresholds.row_tolerance)
    row_words = [tuple(sorted(group, key=lambda w: (w.x0, w.x1, w.text))) for group in groups]
    token_rows = [_token_groups(row, thresholds) for row in row_words]
    centres = _column_centres(token_rows, thresholds)
    provisional = [_cells(tokens, centres, thresholds) for tokens in token_rows]
    valid_rows = [
        i
        for i, (cells, _) in enumerate(provisional)
        if any(c.amount.status in {"ok", "nil"} for c in cells)
    ]
    dates = [
        i
        for i, row in enumerate(row_words)
        if parse_period_end(" ".join(w.text for w in row)) is not None
    ]
    header_end = dates[-1] if dates else (valid_rows[0] - 1 if valid_rows else len(groups) - 1)
    body_cells = [i for i, (cells, _) in enumerate(provisional) if i > header_end and cells]
    last_body = body_cells[-1] if body_cells else header_end
    if not body_cells:
        header_end = last_body = len(groups) - 1
    columns = _columns(centres, row_words, header_end, token_rows, thresholds)
    value_spans = []
    for centre in centres:
        starts = [
            t[0].x0
            for tokens in token_rows[header_end + 1 : last_body + 1]
            for t in tokens
            if abs(t[-1].x1 - centre) <= thresholds.column_tolerance
        ]
        value_spans.append((min(starts, default=centre), centre))

    rows = []
    for i, row in enumerate(row_words):
        zone = "header" if i <= header_end else "body" if i <= last_body else "footer"
        cells, used = provisional[i] if zone == "body" else ((), set())
        label_words = [w for w in row if w not in used]
        top, bottom = min(w.y0 for w in row), max(w.y1 for w in row)
        previous_bottom = rows[-1].y_bottom if rows else None
        rows.append(
            Row(
                i,
                zone,
                top,
                bottom,
                _join_words(label_words, thresholds.label_space_gap),
                label_words[0].x0 if label_words else None,
                None,
                cells,
                _has_rule(raw_page, previous_bottom, top, value_spans, thresholds),
                row,
            )
        )

    labels = [r for r in rows if r.zone == "body" and r.label_x0 is not None]
    indent_groups = _clusters(labels, lambda r: r.label_x0, thresholds.indent_tolerance)
    indent_centres = tuple(median(r.label_x0 for r in group) for group in indent_groups)
    assignments = {r.index: step for step, group in enumerate(indent_groups) for r in group}
    rows = [replace(r, indent_step=assignments.get(r.index)) for r in rows]
    warnings = []
    if not centres:
        warnings.append(
            ParseWarning("no_columns_detected", "no supported numeric columns detected")
        )
    elif len(centres) == 1:
        warnings.append(
            ParseWarning("one_column_detected", "only one supported value column detected")
        )
    if not any(r.zone == "body" for r in rows):
        warnings.append(ParseWarning("no_body_rows", "no body rows reconstructed"))
    return PageLayout(tuple(rows), columns, indent_centres, thresholds, tuple(warnings))
