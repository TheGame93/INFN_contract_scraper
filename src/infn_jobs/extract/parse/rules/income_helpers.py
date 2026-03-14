"""Helper extractors used by income rules."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.normalize.currency import normalize_eur
from infn_jobs.extract.parse.rules.text_windows import iter_adjacent_line_windows

CURRENCY_ANCHORED_RE = re.compile(r"(?:€|euro)\s*([\d][\d.,\s]*)", re.IGNORECASE)
FORMATTED_AMOUNT_RE = re.compile(r"\d[\d.]*,\d{1,2}|\d+\.\d{2}")
BARE_AMOUNT_RE = re.compile(r"[\d][\d.,\s]*")

INSTITUTE_RE = re.compile(
    r"(?:"
    r"Costo\s+a\s+carico\s+dell['\u2019]?Ente|"
    r"Costo\s+istituzionale|"
    r"Importo\s+annuo\s+complessivo|"
    r"Oneri\s+a\s+carico\s+dell['\u2019]?Istituto"
    r")",
    re.IGNORECASE,
)
GROSS_RE = re.compile(
    r"(?:Compenso|Importo|Reddito)\s+lordo|Retribuzione\s+lorda",
    re.IGNORECASE,
)
NET_RE = re.compile(r"(?:Compenso|Importo|Reddito)\s+netto", re.IGNORECASE)

TOTAL_RE = re.compile(r"\b(?:totale|complessiv[oa])\b", re.IGNORECASE)
YEARLY_RE = re.compile(r"\b(?:annuo|annuale)\b", re.IGNORECASE)
MONTHLY_RE = re.compile(r"\bmensile\b", re.IGNORECASE)


def iter_lines(segment_text: str) -> tuple[str, ...]:
    """Return non-empty stripped segment lines preserving source order."""
    return tuple(line.strip() for line in segment_text.splitlines() if line.strip())


def extract_amount(line: str, start_pos: int = 0) -> float | None:
    """Extract amount from one line using stable precedence patterns."""
    for pattern, group in (
        (CURRENCY_ANCHORED_RE, 1),
        (FORMATTED_AMOUNT_RE, 0),
        (BARE_AMOUNT_RE, 0),
    ):
        match = pattern.search(line, pos=start_pos)
        if match is None:
            continue
        value = normalize_eur(match.group(group))
        if value is not None:
            return value
    return None


def line_has_no_qualifier(line: str) -> bool:
    """Return True when line has no total/yearly/monthly qualifier token."""
    return not (TOTAL_RE.search(line) or YEARLY_RE.search(line) or MONTHLY_RE.search(line))


def find_amount(
    *,
    segment_text: str,
    label_re: re.Pattern[str],
    require_total: bool = False,
    require_yearly: bool = False,
    require_monthly: bool = False,
    require_no_qualifier: bool = False,
) -> tuple[float, str] | None:
    """Return last matching `(amount, evidence)` candidate for constraints."""
    candidate: tuple[float, str] | None = None
    for window in iter_adjacent_line_windows(segment_text, max_lines=2):
        label_match = label_re.search(window.text)
        if label_match is None:
            continue
        if require_total and TOTAL_RE.search(window.text) is None:
            continue
        if require_yearly and YEARLY_RE.search(window.text) is None:
            continue
        if require_monthly and MONTHLY_RE.search(window.text) is None:
            continue
        if require_no_qualifier and not line_has_no_qualifier(window.text):
            continue
        amount = extract_amount(window.text, start_pos=label_match.end())
        if amount is None:
            continue
        candidate = (amount, window.evidence)
    return candidate
