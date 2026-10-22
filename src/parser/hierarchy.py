"""Pure indent-stack ancestry with an explicitly partial rules-only fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from parser.classify import ParseWarning, TypedRow


@dataclass(frozen=True)
class TreeRow:
    row_id: int
    typed: TypedRow
    parent_row_id: int | None
    parent: str
    parent_path: str
    level: int
    children: tuple[TreeRow, ...]

    @property
    def label(self) -> str:
        return self.typed.row.label

    @property
    def row_type(self):
        return self.typed.row_type


@dataclass(frozen=True)
class Hierarchy:
    rows: tuple[TreeRow, ...]
    tree: tuple[TreeRow, ...]
    hierarchy_source: Literal["indentation", "rules_fallback"]
    warnings: tuple[ParseWarning, ...]


def build_hierarchy(typed_rows: tuple[TypedRow, ...]) -> Hierarchy:
    """Use strictly smaller indent steps; levels count ancestors, never step numbers.

    With fewer than two distinct steps the first body row is the root. Later
    headers attach to it (nesting unknown), ordinary/subtotal rows to the latest
    header, contra/net rows to the nearest earlier line item, and totals to root.
    This deliberately partial fallback is always warned, including empty input.
    """
    rows = tuple(typed_rows)
    warnings = [w for row in rows for w in row.warnings]
    steps = {r.row.indent_step for r in rows if r.row.indent_step is not None}
    informative = len(steps) >= 2
    source = "indentation" if informative else "rules_fallback"
    parents = []
    if informative:
        stack = []
        previous_step = None
        if rows[0].row.indent_step is not None and rows[0].row.indent_step != min(steps):
            warnings.append(ParseWarning("first_row_not_least_indented", "first row is not least indented", 1))
        for i, row in enumerate(rows):
            step = row.row.indent_step
            if step is None:
                parents.append(stack[-1][0] if stack else None)
                warnings.append(ParseWarning("missing_indent", "row lacks an indent step; attach to active context", i + 1))
                continue
            if previous_step is not None and step - previous_step > 1:
                warnings.append(ParseWarning("skipped_indent", "indent jump exceeds one visual step", i + 1))
            while stack and stack[-1][1] >= step:
                stack.pop()
            parents.append(stack[-1][0] if stack else None)
            stack.append((i, step))
            previous_step = step
    else:
        warnings.append(ParseWarning("insufficient_indentation", "partial rules fallback: header nesting is unknown"))
        latest_header = None
        latest_item = None
        for i, row in enumerate(rows):
            if i == 0:
                parent = None
            elif row.row_type in {"header", "total"}:
                parent = 0
            elif row.row_type in {"contra", "net"}:
                parent = latest_item if latest_item is not None else latest_header
                if parent is None:
                    parent = 0
            else:
                parent = latest_header if latest_header is not None else 0
            parents.append(parent)
            if row.row_type == "header":
                latest_header = i
            elif row.row_type == "line_item":
                latest_item = i

    ancestors = []
    child_indices = {i: [] for i in range(len(rows))}
    roots = []
    for i, parent in enumerate(parents):
        ancestors.append(ancestors[parent] + [parent] if parent is not None else [])
        if parent is None:
            roots.append(i)
        else:
            child_indices[parent].append(i)
    nodes = {}
    for i in reversed(range(len(rows))):
        parent = parents[i]
        nodes[i] = TreeRow(
            i + 1, rows[i], parent + 1 if parent is not None else None,
            rows[parent].row.label if parent is not None else "",
            " > ".join(rows[a].row.label for a in ancestors[i]), len(ancestors[i]),
            tuple(nodes[c] for c in child_indices[i]),
        )
    return Hierarchy(tuple(nodes[i] for i in range(len(rows))),
                     tuple(nodes[i] for i in roots), source, tuple(warnings))
