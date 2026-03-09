"""Extract EUR income and cost fields from a PDF segment."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.normalize.currency import normalize_eur

# Preferred amount patterns:
# 1) amounts explicitly anchored by currency marker (€, euro)
# 2) formatted amounts with decimal separator
# 3) fallback bare number
_CURRENCY_ANCHORED_RE = re.compile(r"(?:€|euro)\s*([\d][\d.,\s]*)", re.IGNORECASE)
_FORMATTED_AMOUNT_RE = re.compile(r"\d[\d.]*,\d{1,2}|\d+\.\d{2}")
_BARE_AMOUNT_RE = re.compile(r"[\d][\d.,\s]*")

# Group: institute cost
_INSTITUTE_RE = re.compile(
    r"(?:Costo\s+a\s+carico\s+dell['\u2019]?Ente|Costo\s+istituzionale)",
    re.IGNORECASE,
)

# Group: gross income (era variants)
_GROSS_RE = re.compile(
    r"(?:Compenso|Importo|Reddito)\s+lordo|Retribuzione\s+lorda",
    re.IGNORECASE,
)

# Group: net income (era variants)
_NET_RE = re.compile(
    r"(?:Compenso|Importo|Reddito)\s+netto",
    re.IGNORECASE,
)

# Qualifier
_TOTAL_RE = re.compile(r"\btotale\b", re.IGNORECASE)
_YEARLY_RE = re.compile(r"\b(?:annuo|annuale)\b", re.IGNORECASE)
_MONTHLY_RE = re.compile(r"\bmensile\b", re.IGNORECASE)


def _extract_amount(line: str, start_pos: int = 0) -> float | None:
    """Extract an amount from a line, preferring currency-anchored matches."""
    for pattern, group in (
        (_CURRENCY_ANCHORED_RE, 1),
        (_FORMATTED_AMOUNT_RE, 0),
        (_BARE_AMOUNT_RE, 0),
    ):
        m = pattern.search(line, pos=start_pos)
        if not m:
            continue
        amount = normalize_eur(m.group(group))
        if amount is not None:
            return amount
    return None


def extract_income(segment: str) -> dict:
    """Extract all 7 EUR income/cost fields and 3 evidence fields from a segment.

    Returns dict with keys: institute_cost_total_eur, institute_cost_yearly_eur,
    gross_income_total_eur, gross_income_yearly_eur, net_income_total_eur,
    net_income_yearly_eur, net_income_monthly_eur, institute_cost_evidence,
    gross_income_evidence, net_income_evidence.
    All values are float | None (EUR fields) or str | None (evidence fields).
    """
    result: dict = {
        "institute_cost_total_eur": None,
        "institute_cost_yearly_eur": None,
        "gross_income_total_eur": None,
        "gross_income_yearly_eur": None,
        "net_income_total_eur": None,
        "net_income_yearly_eur": None,
        "net_income_monthly_eur": None,
        "institute_cost_evidence": None,
        "gross_income_evidence": None,
        "net_income_evidence": None,
    }

    for line in segment.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        institute_match = _INSTITUTE_RE.search(stripped)
        if institute_match:
            amount = _extract_amount(stripped, institute_match.end())
            if amount is not None:
                if _TOTAL_RE.search(stripped):
                    result["institute_cost_total_eur"] = amount
                elif _YEARLY_RE.search(stripped):
                    result["institute_cost_yearly_eur"] = amount
                else:
                    # Default: total if no qualifier
                    result["institute_cost_total_eur"] = amount
                result["institute_cost_evidence"] = stripped

        gross_match = _GROSS_RE.search(stripped)
        if gross_match:
            amount = _extract_amount(stripped, gross_match.end())
            if amount is not None:
                if _TOTAL_RE.search(stripped):
                    result["gross_income_total_eur"] = amount
                elif _YEARLY_RE.search(stripped):
                    result["gross_income_yearly_eur"] = amount
                else:
                    result["gross_income_yearly_eur"] = amount
                result["gross_income_evidence"] = stripped

        net_match = _NET_RE.search(stripped)
        if net_match:
            amount = _extract_amount(stripped, net_match.end())
            if amount is not None:
                if _MONTHLY_RE.search(stripped):
                    result["net_income_monthly_eur"] = amount
                elif _TOTAL_RE.search(stripped):
                    result["net_income_total_eur"] = amount
                elif _YEARLY_RE.search(stripped):
                    result["net_income_yearly_eur"] = amount
                else:
                    result["net_income_yearly_eur"] = amount
                result["net_income_evidence"] = stripped

    return result
