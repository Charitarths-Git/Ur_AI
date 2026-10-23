"""Backend-neutral immutable layout evidence; no semantic hierarchy or row roles."""

from dataclasses import dataclass
from typing import Literal

from parser.normalize import AmountResult


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    size: float | None = None


@dataclass(frozen=True)
class Rule:
    x0: float
    y0: float
    x1: float
    y1: float
    height: float


@dataclass(frozen=True)
class RawPage:
    width: float
    height: float
    words: tuple[Word, ...] = ()
    rules: tuple[Rule, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "words", tuple(self.words))
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True)
class LayoutConfig:
    """All distances multiply median positive word bbox height, not font size.

    row_tolerance: absorb baseline jitter without merging typical adjacent rows.
    column_tolerance: absorb right-edge jitter while keeping columns separate.
    column_min_support: distinct supporting rows, never a token count.
    label_space_gap: preserve large gaps between label tokens as spaces.
    sign_gap: join an immediately preceding sign to its numeric token.
    indent_tolerance: group slightly jittered left edges into visual steps.
    rule_max_height / rule_min_width: reject shading and nonhorizontal shapes.
    rule_vertical_tolerance: small slack at row boundaries for rule evidence.
    single_column_heading_pad: extend a lone column's observed value span left.
    fallback_height_fraction: page-height fraction only if no positive word height.
    """

    row_tolerance: float = 0.35
    column_tolerance: float = 0.30
    column_min_support: int = 3
    label_space_gap: float = 0.35
    sign_gap: float = 0.60
    indent_tolerance: float = 0.40
    rule_max_height: float = 0.15
    rule_min_width: float = 2.0
    rule_vertical_tolerance: float = 0.10
    single_column_heading_pad: float = 2.0
    fallback_height_fraction: float = 0.01

    def __post_init__(self):
        if self.column_min_support < 1:
            raise ValueError("column_min_support must be positive")
        for name in self.__dataclass_fields__:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True)
class LayoutThresholds:
    """Actual distances used, in the input page's coordinate units."""

    median_word_height: float
    row_tolerance: float
    column_tolerance: float
    label_space_gap: float
    sign_gap: float
    indent_tolerance: float
    rule_max_height: float
    rule_min_width: float
    rule_vertical_tolerance: float
    single_column_heading_pad: float
    column_min_support: int


@dataclass(frozen=True)
class Column:
    index: int
    x1_centre: float
    heading: str
    period_end: tuple[int, int, int] | None


@dataclass(frozen=True)
class Cell:
    column_index: int
    raw: str
    amount: AmountResult


@dataclass(frozen=True)
class Row:
    index: int
    zone: Literal["header", "body", "footer"]
    y_top: float
    y_bottom: float
    label: str
    label_x0: float | None
    indent_step: int | None
    cells: tuple[Cell, ...]
    rule_above: bool
    source_words: tuple[Word, ...]


@dataclass(frozen=True)
class ParseWarning:
    code: str
    message: str
    row_id: int | None = None


@dataclass(frozen=True)
class PageLayout:
    rows: tuple[Row, ...]
    columns: tuple[Column, ...]
    indent_centres: tuple[float, ...]
    thresholds: LayoutThresholds
    warnings: tuple[ParseWarning, ...] = ()
