"""Helper extractors used by duration rules."""

from __future__ import annotations

import re

_LABEL_RE = re.compile(
    r"(?:Durata|Periodo|per\s+la\s+durata\s+di|della\s+durata\s+di)\s*:?\s*(.+)",
    re.IGNORECASE,
)
_NUMERIC_RE = re.compile(r"(\d+)(?:\s*\([^)]*\))?\s*mes[ei]", re.IGNORECASE)
_ONE_MONTH_RE = re.compile(r"\bun(?:o)?\s+mes[ei]\b", re.IGNORECASE)
_TRIENNALE_RE = re.compile(r"\btriennale\b", re.IGNORECASE)
_BIENNALE_RE = re.compile(r"\bbiennale\b", re.IGNORECASE)
_ANNUALE_RE = re.compile(r"\b(?:annuale|annuo)\b", re.IGNORECASE)
_FALLBACK_BARE_RE = re.compile(r"^(?:triennale|biennale|annuale|annuo)\W*$", re.IGNORECASE)
_FALLBACK_CONTEXT_RE = re.compile(
    r"\b(?:durata|rinnovabile|usufruire|borsa|assegno|contratto|incarico|attivit[àa])\b",
    re.IGNORECASE,
)
_GUARD_CONTEXT_RE = re.compile(r"\b(?:durata|periodo|rinnovabile|usufruire)\b", re.IGNORECASE)


def iter_nonempty_lines(text: str) -> tuple[str, ...]:
    """Return non-empty stripped lines preserving source order."""
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def extract_labeled_value_text(segment_text: str) -> tuple[str, str] | None:
    """Return `(value_text, evidence_line)` for the first labeled duration line."""
    for line in iter_nonempty_lines(segment_text):
        match = _LABEL_RE.search(line)
        if match:
            return match.group(1), line
    return None


def extract_labeled_numeric(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for numeric labeled duration."""
    labeled = extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    match = _NUMERIC_RE.search(value_text)
    if match is None:
        return None
    return int(match.group(1)), match.group(0).strip(), evidence


def extract_labeled_one_month(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for labeled one-month duration."""
    labeled = extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    if _ONE_MONTH_RE.search(value_text):
        return 1, "un mese", evidence
    return None


def extract_labeled_triennale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for labeled triennale duration."""
    return _extract_labeled_word(segment_text, pattern=_TRIENNALE_RE, months=36, raw="triennale")


def extract_labeled_biennale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for labeled biennale duration."""
    return _extract_labeled_word(segment_text, pattern=_BIENNALE_RE, months=24, raw="biennale")


def extract_labeled_annuale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for labeled annuale/annuo duration."""
    return _extract_labeled_word(segment_text, pattern=_ANNUALE_RE, months=12, raw="annuale")


def extract_bare_triennale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for fallback triennale duration."""
    return _extract_bare_word(segment_text, pattern=_TRIENNALE_RE, months=36, raw="triennale")


def extract_bare_biennale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for fallback biennale duration."""
    return _extract_bare_word(segment_text, pattern=_BIENNALE_RE, months=24, raw="biennale")


def extract_bare_annuale(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for fallback annuale/annuo duration."""
    return _extract_bare_word(segment_text, pattern=_ANNUALE_RE, months=12, raw="annuale")


def extract_numeric_guarded(segment_text: str) -> tuple[int, str, str] | None:
    """Return `(months, raw, evidence)` for guard-tier numeric duration."""
    for line in iter_nonempty_lines(segment_text):
        if not _GUARD_CONTEXT_RE.search(line):
            continue
        match = _NUMERIC_RE.search(line)
        if match:
            return int(match.group(1)), match.group(0).strip(), line
    return None


def has_duration_context(segment_text: str) -> bool:
    """Return True when segment includes duration-like context words."""
    return _FALLBACK_CONTEXT_RE.search(segment_text) is not None


def _extract_labeled_word(
    segment_text: str,
    *,
    pattern: re.Pattern[str],
    months: int,
    raw: str,
) -> tuple[int, str, str] | None:
    labeled = extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    if pattern.search(value_text):
        return months, raw, evidence
    return None


def _extract_bare_word(
    segment_text: str,
    *,
    pattern: re.Pattern[str],
    months: int,
    raw: str,
) -> tuple[int, str, str] | None:
    for line in iter_nonempty_lines(segment_text):
        if not pattern.search(line):
            continue
        if _FALLBACK_BARE_RE.match(line) or _FALLBACK_CONTEXT_RE.search(line):
            return months, raw, line
    return None
