"""Pure normalization helpers; no file access, accounting rules or scaling.

Decisions:
- Amounts are whole printed units (千円): decimals, units and unexpected symbols
  are invalid. Non-string inputs are invalid and retained unchanged as raw.
- Dash-only runs, allowing whitespace, are nil. Any one of the listed dashes
  before digits is negative; repeated/mixed signs are invalid. Whitespace after
  a sign or inside parentheses is allowed; whitespace splitting digits is not.
- Parentheses mean negative and cannot be combined with another sign. All
  printed negative zeros retain negative=True and note "negative zero printed".
- Comma groups must be nonempty, but unusual widths are accepted with a note.
  A leading group of 1–3 digits is normal; later groups normally have 3 digits.
- Large integers use bounded chunks, avoiding Python's string-to-int digit cap
  without changing process-wide settings.
- Label keys are for COMPARISON ONLY. Output labels remain exactly as printed.
  NFKC is repeated after whitespace removal to compose newly adjacent marks,
  keeping keys idempotent even when whitespace separated a combining character.
- Periods require a four-digit Gregorian year and a real calendar date. The
  first complete date is used. Japanese-era (和暦) conversion is not supported.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Literal

AmountStatus = Literal["ok", "nil", "invalid", "empty"]

_DASHES = frozenset("－―—–−‐ー-")
_NEGATIVES = _DASHES | frozenset("△▲")
_INTEGER = re.compile(r"[0-9]+(?:,[0-9]+)*")
_PERIOD = re.compile(r"(?<![0-9])([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日")


@dataclass(frozen=True)
class AmountResult:
    """Lossless raw input plus an integer/null and explicit parsing outcome.

    ``negative`` describes a successfully parsed negative representation;
    it is False for nil, empty and invalid inputs. Notes are informational.
    """

    raw: object
    value: int | None
    status: AmountStatus
    negative: bool = False
    note: str = ""


def parse_amount(raw: object) -> AmountResult:
    """Parse printed integer units without scaling or raising for malformed input.

    Only strings can be valid amounts. The exact original input is retained,
    including surrounding whitespace and full-width characters.
    """
    if not isinstance(raw, str):
        return AmountResult(raw, None, "invalid", note="expected text input")
    text = raw.strip()
    if not text:
        return AmountResult(raw, None, "empty")
    if all(char in _DASHES or char.isspace() for char in text):
        return AmountResult(raw, None, "nil")

    text = unicodedata.normalize("NFKC", text)
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    elif "(" in text or ")" in text:
        return AmountResult(raw, None, "invalid", note="unmatched or misplaced parentheses")
    if text and text[0] in _NEGATIVES:
        if negative:
            return AmountResult(raw, None, "invalid", note="multiple negative markers")
        negative = True
        text = text[1:].strip()
        if text and text[0] in _NEGATIVES:
            return AmountResult(raw, None, "invalid", note="multiple negative markers")

    if not text:
        return AmountResult(raw, None, "invalid", note="missing digits")
    if "千円" in text or "円" in text:
        return AmountResult(raw, None, "invalid", note="unit suffix is not allowed")
    if "." in text:
        return AmountResult(raw, None, "invalid", note="decimals are not supported")
    if any(char.isspace() for char in text):
        return AmountResult(raw, None, "invalid", note="internal whitespace or multiple numbers")
    if not _INTEGER.fullmatch(text):
        reason = "malformed comma separators" if "," in text else "unexpected characters or sign"
        return AmountResult(raw, None, "invalid", note=reason)

    groups = text.split(",")
    notes = []
    if len(groups) > 1 and (len(groups[0]) > 3 or any(len(g) != 3 for g in groups[1:])):
        notes.append("nonstandard comma grouping")
    digits = "".join(groups)
    value = 0
    for offset in range(0, len(digits), 500):
        chunk = digits[offset:offset + 500]
        value = value * 10 ** len(chunk) + int(chunk)
    if negative:
        value = -value
        if value == 0:
            notes.insert(0, "negative zero printed")
    return AmountResult(raw, value, "ok", negative, "; ".join(notes))


def label_key(label: str) -> str:
    """Return an idempotent NFKC key without whitespace, for COMPARISON ONLY.

    Never use the key as an output label: keep the printed label, including
    full-width （純額） and any printed spaces, in exported data.
    """
    normalized = unicodedata.normalize("NFKC", label)
    return unicodedata.normalize("NFKC", "".join(normalized.split()))


def labels_equal(a: str, b: str) -> bool:
    """Compare labels using matching keys without modifying either label."""
    return label_key(a) == label_key(b)


def parse_period_end(text: str) -> tuple[int, int, int] | None:
    """Extract the first complete Gregorian date; invalid/absent dates return None.

    Full-width digits and arbitrary whitespace are supported. No Japanese-era
    (和暦) conversion is performed. Impossible dates are rejected.
    """
    if not isinstance(text, str):
        return None
    normalized = "".join(unicodedata.normalize("NFKC", text).split())
    match = _PERIOD.search(normalized)
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        date(year, month, day)
    except ValueError:
        return None
    return year, month, day
