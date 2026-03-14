"""Core orchestrator for rule-driven parser execution."""

from __future__ import annotations

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.core.execution_shared import _execute_segments, _ExecutedSegment
from infn_jobs.extract.parse.core.models import ParseRequest, ParseResult
from infn_jobs.extract.parse.fields.confidence import score_confidence


def _assign_parse_confidence(row: PositionRow) -> None:
    """Assign parse_confidence using only assembled row outcomes."""
    row.parse_confidence = score_confidence(row).value


def _build_row(
    *,
    detail_id: str,
    text_quality: str,
    segment: _ExecutedSegment,
) -> PositionRow:
    """Build one PositionRow from shared segment execution artifacts."""
    identity = segment.identity
    duration = segment.duration
    income = segment.income
    section = segment.section

    return PositionRow(
        detail_id=detail_id,
        position_row_index=segment.segment_index,
        text_quality=text_quality,
        contract_type=identity.contract_type,
        contract_type_raw=identity.contract_type_raw,
        contract_type_evidence=identity.contract_type_evidence,
        contract_subtype=identity.contract_subtype,
        contract_subtype_raw=identity.contract_subtype_raw,
        contract_subtype_evidence=identity.contract_subtype_evidence,
        duration_months=duration.duration_months,
        duration_raw=duration.duration_raw,
        duration_evidence=duration.evidence,
        section_structure_department=section.value,
        section_evidence=section.evidence,
        institute_cost_total_eur=income.values["institute_cost_total_eur"],
        institute_cost_yearly_eur=income.values["institute_cost_yearly_eur"],
        gross_income_total_eur=income.values["gross_income_total_eur"],
        gross_income_yearly_eur=income.values["gross_income_yearly_eur"],
        net_income_total_eur=income.values["net_income_total_eur"],
        net_income_yearly_eur=income.values["net_income_yearly_eur"],
        net_income_monthly_eur=income.values["net_income_monthly_eur"],
        institute_cost_evidence=income.values["institute_cost_evidence"],
        gross_income_evidence=income.values["gross_income_evidence"],
        net_income_evidence=income.values["net_income_evidence"],
    )


def run_parse_pipeline(request: ParseRequest) -> ParseResult:
    """Build PositionRow values through the rule-driven parser pipeline."""
    if not request.text or request.text_quality == "no_text":
        return ParseResult(rows=[], pdf_call_title=None)

    execution = _execute_segments(text=request.text, detail_id=request.detail_id, anno=request.anno)
    rows: list[PositionRow] = []
    for segment in execution.segments:
        row = _build_row(
            detail_id=request.detail_id,
            text_quality=request.text_quality,
            segment=segment,
        )
        _assign_parse_confidence(row)
        rows.append(row)

    return ParseResult(rows=rows, pdf_call_title=execution.pdf_call_title)
