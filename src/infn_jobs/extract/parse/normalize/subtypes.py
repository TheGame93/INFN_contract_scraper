"""Normalize contract subtype strings to canonical form."""

from __future__ import annotations

import re

# Tipo A/B require post-2010 era
_TIPO_AB = re.compile(r"tipo\s+([ab])", re.IGNORECASE)
_FASCIA_II = re.compile(r"fascia\s+ii", re.IGNORECASE)


def normalize_subtype(s: str | None, anno: int | None) -> str | None:
    """Normalize contract subtype string to canonical form. Era-aware for Assegno subtypes."""
    if not s:
        return None

    stripped = s.strip()

    # Fascia II → Fascia 2 (no era gate)
    if _FASCIA_II.search(stripped):
        return "Fascia 2"

    # Tipo A / Tipo B — era-gated: post-2010 only
    m = _TIPO_AB.search(stripped)
    if m:
        if anno is None or anno < 2010:
            return None
        return f"Tipo {m.group(1).upper()}"

    # Unrecognized subtype — pass through normalized (strip + title-case) if post-2010
    if anno is not None and anno >= 2010:
        return stripped.title()

    return None
