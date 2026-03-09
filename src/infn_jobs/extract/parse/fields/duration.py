"""Extract duration from a PDF segment."""

from __future__ import annotations

import re

# Label variants
_LABEL_RE = re.compile(
    r"(?:Durata|Periodo|per\s+la\s+durata\s+di|della\s+durata\s+di)\s*:?\s*(.+)",
    re.IGNORECASE,
)

# Numeric with optional parenthetical: "12 mesi", "24 (venti quattro) mesi"
_NUMERIC_RE = re.compile(r"(\d+)(?:\s*\([^)]*\))?\s*mes[ei]", re.IGNORECASE)

# Word-based
_WORD_MAP: list[tuple[re.Pattern, int, str]] = [
    (re.compile(r"\btriennale\b", re.IGNORECASE), 36, "triennale"),
    (re.compile(r"\bbiennale\b", re.IGNORECASE), 24, "biennale"),
    (re.compile(r"\b(?:annuale|annuo)\b", re.IGNORECASE), 12, "annuale"),
]


def _parse_duration_value(value_text: str) -> tuple[int | None, str | None]:
    """Return (months, raw_string) from the text after a duration label."""
    # Numeric first
    m = _NUMERIC_RE.search(value_text)
    if m:
        raw = m.group(0).strip()
        return int(m.group(1)), raw

    # Word-based
    for pattern, months, raw in _WORD_MAP:
        if pattern.search(value_text):
            return months, raw

    return None, None


def extract_duration(segment: str) -> tuple[int | None, str | None, str | None]:
    """Extract duration from a segment. Returns (duration_months, duration_raw, evidence)."""
    for line in segment.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        m = _LABEL_RE.search(stripped)
        if m:
            months, raw = _parse_duration_value(m.group(1))
            if months is not None:
                return months, raw, stripped

        # Also try word-based match without a label (e.g. bare "biennale" line)
        for pattern, months, raw in _WORD_MAP:
            if pattern.search(stripped):
                return months, raw, stripped

    return None, None, None
