"""Compute parse_confidence for a PositionRow."""

from __future__ import annotations

from infn_jobs.domain.enums import ParseConfidence, TextQuality
from infn_jobs.domain.position import PositionRow

_EUR_FIELDS = (
    "institute_cost_total_eur",
    "institute_cost_yearly_eur",
    "gross_income_total_eur",
    "gross_income_yearly_eur",
    "net_income_total_eur",
    "net_income_yearly_eur",
    "net_income_monthly_eur",
)


def score_confidence(row: PositionRow, text_quality: str) -> ParseConfidence:
    """Compute parse_confidence for a PositionRow based on parsed fields and text quality."""
    # LOW: garbled or empty source text
    if text_quality in (TextQuality.OCR_DEGRADED.value, TextQuality.NO_TEXT.value):
        return ParseConfidence.LOW

    has_eur = any(getattr(row, f) is not None for f in _EUR_FIELDS)

    # HIGH: duration + at least one EUR field
    if row.duration_months is not None and has_eur:
        return ParseConfidence.HIGH

    # MEDIUM: contract_type parsed but no EUR fields
    if row.contract_type is not None:
        return ParseConfidence.MEDIUM

    # LOW: nothing meaningful extracted from readable text
    return ParseConfidence.LOW
