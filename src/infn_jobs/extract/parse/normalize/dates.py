"""Parse DD-MM-YYYY and DD/MM/YYYY date strings."""

from __future__ import annotations

from datetime import date


def parse_date(s: str | None) -> date | None:
    """Parse a date string in DD-MM-YYYY or DD/MM/YYYY format. Returns None if invalid."""
    # NOTE: shared infrastructure for v2/v3; currently not used by v1 production code.
    if not s:
        return None

    s = s.strip()
    # Accept only the two explicit separators
    if "-" in s:
        parts = s.split("-")
    elif "/" in s:
        parts = s.split("/")
    else:
        return None

    if len(parts) != 3:
        return None

    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, OverflowError):
        return None
