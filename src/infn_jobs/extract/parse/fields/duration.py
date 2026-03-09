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
_ONE_MONTH_RE = re.compile(r"\bun(?:o)?\s+mes[ei]\b", re.IGNORECASE)

# Word-based
_WORD_MAP: list[tuple[re.Pattern, int, str]] = [
    (re.compile(r"\btriennale\b", re.IGNORECASE), 36, "triennale"),
    (re.compile(r"\bbiennale\b", re.IGNORECASE), 24, "biennale"),
    (re.compile(r"\b(?:annuale|annuo)\b", re.IGNORECASE), 12, "annuale"),
]
_FALLBACK_BARE_RE = re.compile(r"^(?:triennale|biennale|annuale|annuo)\W*$", re.IGNORECASE)
_FALLBACK_CONTEXT_RE = re.compile(
    r"\b(?:durata|rinnovabile|usufruire|borsa|assegno|contratto|incarico|attivit[àa])\b",
    re.IGNORECASE,
)


def _parse_duration_value(value_text: str) -> tuple[int | None, str | None]:
    """Return (months, raw_string) from the text after a duration label."""
    # Numeric first
    m = _NUMERIC_RE.search(value_text)
    if m:
        raw = m.group(0).strip()
        return int(m.group(1)), raw

    # Common textual variant
    if _ONE_MONTH_RE.search(value_text):
        return 1, "un mese"

    # Word-based
    for pattern, months, raw in _WORD_MAP:
        if pattern.search(value_text):
            return months, raw

    return None, None


def _parse_bare_duration_line(line: str) -> tuple[int | None, str | None]:
    """Return duration from a bare-word fallback line only in duration-like contexts."""
    for pattern, months, raw in _WORD_MAP:
        if not pattern.search(line):
            continue
        if _FALLBACK_BARE_RE.match(line) or _FALLBACK_CONTEXT_RE.search(line):
            return months, raw
    return None, None


def extract_duration(segment: str) -> tuple[int | None, str | None, str | None]:
    """Extract duration from a segment. Returns (duration_months, duration_raw, evidence)."""
    lines = [line.strip() for line in segment.splitlines() if line.strip()]

    # Pass 1: explicit labeled duration lines.
    for stripped in lines:
        m = _LABEL_RE.search(stripped)
        if not m:
            continue
        months, raw = _parse_duration_value(m.group(1))
        if months is not None:
            return months, raw, stripped

    # Pass 2: bare duration words in duration-like context only.
    for stripped in lines:
        months, raw = _parse_bare_duration_line(stripped)
        if months is not None:
            return months, raw, stripped

    return None, None, None
