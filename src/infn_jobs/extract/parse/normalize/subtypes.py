"""Normalize contract subtype strings to canonical form."""

from __future__ import annotations

import re

# Tipo A/B require post-2010 era.
_TIPO_AB = re.compile(r"tipo\s+([ab])", re.IGNORECASE)
_JUNIOR = re.compile(r"\bjunior\b", re.IGNORECASE)
_SENIOR = re.compile(r"\bsenior\b", re.IGNORECASE)
_FASCIA_LEVEL = re.compile(r"fascia\s+(i{1,3}|[123])", re.IGNORECASE)
_ROMAN_LEVEL_TO_DIGIT = {"i": "1", "ii": "2", "iii": "3"}


def normalize_subtype(s: str | None, anno: int | None) -> str | None:
    """Normalize contract subtype string to canonical form. Era-aware for Assegno subtypes."""
    if not s:
        return None

    stripped = s.strip()

    # Fascia I/II/III and Fascia 1/2/3 -> canonical Fascia <digit> (no era gate).
    fascia_match = _FASCIA_LEVEL.search(stripped)
    if fascia_match:
        level = fascia_match.group(1).lower()
        normalized_level = _ROMAN_LEVEL_TO_DIGIT.get(level, level)
        return f"Fascia {normalized_level}"

    # Tipo A / Tipo B — era-gated: post-2010 only.
    m = _TIPO_AB.search(stripped)
    if m:
        if anno is None or anno < 2010:
            return None
        return "Junior" if m.group(1).lower() == "a" else "Senior"

    # Assegno canonical semantics.
    if _JUNIOR.search(stripped):
        return "Junior"
    if _SENIOR.search(stripped):
        return "Senior"

    # Unrecognized subtype — pass through normalized (strip + title-case) if post-2010
    if anno is not None and anno >= 2010:
        return stripped.title()

    return None
