"""Assemble PositionRow list from mutool PDF text."""

from __future__ import annotations

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.fields.confidence import score_confidence
from infn_jobs.extract.parse.fields.contract_type import extract_contract_type
from infn_jobs.extract.parse.fields.duration import extract_duration
from infn_jobs.extract.parse.fields.income import extract_income
from infn_jobs.extract.parse.fields.metadata import (
    extract_pdf_call_title,
    extract_section_department,
)
from infn_jobs.extract.parse.segmenter import segment


def build_rows(
    text: str,
    detail_id: str,
    text_quality: str,
    anno: int | None,
) -> tuple[list[PositionRow], str | None]:
    """Segment text and build PositionRow list. Second element is pdf_call_title (call-level)."""
    if not text or text_quality == "no_text":
        return [], None

    pdf_call_title = extract_pdf_call_title(text)
    segments = segment(text)
    rows: list[PositionRow] = []

    for i, seg in enumerate(segments):
        ct = extract_contract_type(seg, anno)
        dur_months, dur_raw, dur_ev = extract_duration(seg)
        income = extract_income(seg)
        section, section_ev = extract_section_department(seg)

        row = PositionRow(
            detail_id=detail_id,
            position_row_index=i,
            text_quality=text_quality,
            contract_type=ct["contract_type"],
            contract_type_raw=ct["contract_type_raw"],
            contract_type_evidence=ct["contract_type_evidence"],
            contract_subtype=ct["contract_subtype"],
            contract_subtype_raw=ct["contract_subtype_raw"],
            contract_subtype_evidence=ct["contract_subtype_evidence"],
            duration_months=dur_months,
            duration_raw=dur_raw,
            duration_evidence=dur_ev,
            section_structure_department=section,
            section_evidence=section_ev,
            institute_cost_total_eur=income["institute_cost_total_eur"],
            institute_cost_yearly_eur=income["institute_cost_yearly_eur"],
            gross_income_total_eur=income["gross_income_total_eur"],
            gross_income_yearly_eur=income["gross_income_yearly_eur"],
            net_income_total_eur=income["net_income_total_eur"],
            net_income_yearly_eur=income["net_income_yearly_eur"],
            net_income_monthly_eur=income["net_income_monthly_eur"],
            institute_cost_evidence=income["institute_cost_evidence"],
            gross_income_evidence=income["gross_income_evidence"],
            net_income_evidence=income["net_income_evidence"],
        )
        row.parse_confidence = score_confidence(row, text_quality).value
        rows.append(row)

    return rows, pdf_call_title
