"""Extract EUR income and cost fields from a PDF segment."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.normalize.currency import normalize_eur

# Amount pattern: captures Italian or standard number with optional € prefix
_AMOUNT_RE = re.compile(r"[€]?\s*[\d][\d.,\s]*")

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


def _extract_amount(line: str) -> float | None:
    m = _AMOUNT_RE.search(line)
    if m:
        return normalize_eur(m.group(0))
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

        if _INSTITUTE_RE.search(stripped):
            amount = _extract_amount(stripped)
            if amount is not None:
                if _TOTAL_RE.search(stripped):
                    result["institute_cost_total_eur"] = amount
                elif _YEARLY_RE.search(stripped):
                    result["institute_cost_yearly_eur"] = amount
                else:
                    # Default: total if no qualifier
                    result["institute_cost_total_eur"] = amount
                result["institute_cost_evidence"] = stripped

        elif _GROSS_RE.search(stripped):
            amount = _extract_amount(stripped)
            if amount is not None:
                if _TOTAL_RE.search(stripped):
                    result["gross_income_total_eur"] = amount
                elif _YEARLY_RE.search(stripped):
                    result["gross_income_yearly_eur"] = amount
                else:
                    result["gross_income_yearly_eur"] = amount
                result["gross_income_evidence"] = stripped

        elif _NET_RE.search(stripped):
            amount = _extract_amount(stripped)
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
