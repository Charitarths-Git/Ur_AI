"""Replaceable language patterns. Only the page-4 subset has real-document validation."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from parser.normalize import label_key


@dataclass(frozen=True)
class RuleSet:
    total_labels: tuple[str, ...] = ()
    total_suffixes: tuple[str, ...] = ()
    subtotal_suffixes: tuple[str, ...] = ()
    net_suffixes: tuple[str, ...] = ()
    contra_labels: tuple[str, ...] = ()
    unit_pattern: str = r"(?!)"
    unit_multipliers: Mapping[str, int] = field(default_factory=dict)
    correction_markers: tuple[tuple[str, str], ...] = ()
    page_number_pattern: str = r"(?!)"

    def __post_init__(self):
        for name in ("total_labels", "total_suffixes", "subtotal_suffixes", "net_suffixes",
                     "contra_labels", "correction_markers"):
            value = getattr(self, name)
            if name == "correction_markers":
                value = tuple(tuple(pair) for pair in value)
            object.__setattr__(self, name, tuple(value))
        object.__setattr__(self, "unit_multipliers", MappingProxyType(dict(self.unit_multipliers)))

    def exact(self, label: str, patterns: tuple[str, ...]) -> bool:
        return label_key(label) in {label_key(p) for p in patterns}

    def suffix(self, label: str, patterns: tuple[str, ...]) -> bool:
        return any(label_key(label).endswith(label_key(p)) for p in patterns)

    def prefix(self, label: str, patterns: tuple[str, ...]) -> bool:
        return any(label_key(label).startswith(label_key(p)) for p in patterns)


JA_FINANCIAL_STATEMENT = RuleSet(
    total_labels=("資産合計", "負債純資産合計", "負債及び純資産合計", "負債・純資産合計"),
    subtotal_suffixes=("合計",),
    net_suffixes=("（純額）", "(純額)"),
    contra_labels=("減価償却累計額", "貸倒引当金", "自己株式"),
    unit_pattern=r"\(単位:(?P<unit>[^()]+)\)",
    unit_multipliers={"千円": 1000, "百万円": 1000000, "円": 1},
    correction_markers=(("（訂正後）", "訂正後"), ("（訂正前）", "訂正前")),
    page_number_pattern=r"-(?P<page>[0-9]+)-",
)
