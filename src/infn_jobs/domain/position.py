"""PositionRow dataclass representing one contract entry extracted from a PDF."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PositionRow:
    """One contract line extracted from a PDF; every field is nullable."""

    detail_id: str | None = None
    position_row_index: int | None = None
    text_quality: str | None = None
    contract_type: str | None = None
    contract_type_raw: str | None = None
    contract_subtype: str | None = None
    contract_subtype_raw: str | None = None
    duration_months: int | None = None
    duration_raw: str | None = None
    section_structure_department: str | None = None
    institute_cost_total_eur: float | None = None
    institute_cost_yearly_eur: float | None = None
    gross_income_total_eur: float | None = None
    gross_income_yearly_eur: float | None = None
    net_income_total_eur: float | None = None
    net_income_yearly_eur: float | None = None
    net_income_monthly_eur: float | None = None
    contract_type_evidence: str | None = None
    contract_subtype_evidence: str | None = None
    duration_evidence: str | None = None
    section_evidence: str | None = None
    institute_cost_evidence: str | None = None
    gross_income_evidence: str | None = None
    net_income_evidence: str | None = None
    parse_confidence: str | None = None
