"""Pure metadata helpers; language-specific patterns are supplied by the caller."""

import re

from parser.normalize import label_key


def clean_column_heading(heading: str, unit_pattern: str) -> str:
    """Remove whole unit lines from metadata headings, preserving other text.

    P4 keeps its original geometric heading evidence. Apply the caller's pattern
    to comparison keys only, so emitted headings keep printed characters.
    """
    return "\n".join(line for line in heading.splitlines()
                     if not re.fullmatch(unit_pattern, label_key(line)))
