"""Normalize Italian-format EUR strings to float."""

from __future__ import annotations

import re


def normalize_eur(s: str | None) -> float | None:
    """Normalize Italian-format EUR string to float. Returns None if unparseable."""
    if s is None:
        return None

    # Collapse whitespace/line breaks first
    cleaned = re.sub(r"\s+", " ", s).strip()

    # Strip currency symbols and labels
    cleaned = re.sub(r"[€EUReur]+", "", cleaned).strip()

    # Remove any remaining non-numeric characters except . and ,
    cleaned = re.sub(r"[^\d.,]", "", cleaned)

    if not cleaned:
        return None

    try:
        if "," in cleaned:
            # Italian format: thousands sep = '.', decimal sep = ','
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif re.search(r"\.\d{3}$", cleaned):
            # Dot followed by exactly 3 digits at end → thousands separator (e.g. "1.200")
            cleaned = cleaned.replace(".", "")
        # else: standard decimal point (e.g. "1200.50") or plain integer
        return float(cleaned)
    except ValueError:
        return None
