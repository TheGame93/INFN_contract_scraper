"""Compatibility orchestrator for parser execution."""

from __future__ import annotations

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.core.classification import classify_segments
from infn_jobs.extract.parse.core.models import ParseRequest, ParseResult
from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed
from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.fields.confidence import score_confidence
from infn_jobs.extract.parse.fields.duration import extract_duration
from infn_jobs.extract.parse.fields.income import extract_income
from infn_jobs.extract.parse.fields.metadata import extract_pdf_call_title
from infn_jobs.extract.parse.rules.contract_identity import (
    ContractIdentityResolution,
    resolve_contract_identity,
)
from infn_jobs.extract.parse.rules.models import ExecutionResult
from infn_jobs.extract.parse.rules.section import resolve_section


def _record_execution_events(
    *,
    diagnostics: EventCollector,
    detail_id: str,
    result: ExecutionResult,
    field_name: str,
    source_line_start: int | None,
    source_line_end: int | None,
) -> None:
    """Record winner and rejected rule events for one field resolution."""
    for rejected in result.rejected:
        diagnostics.record_rejected(
            detail_id=detail_id,
            rejected=rejected,
            source_line_start=source_line_start,
            source_line_end=source_line_end,
        )
    if result.winner is not None:
        diagnostics.record_winner(
            detail_id=detail_id,
            field_name=field_name,
            candidate=result.winner,
            source_line_start=source_line_start,
            source_line_end=source_line_end,
        )


def _resolve_identity(
    *,
    segment_text: str,
    anno: int | None,
    predicted_contract_type: str | None,
    detail_id: str,
) -> ContractIdentityResolution:
    """Resolve profile-aware contract identity fields for one segment."""
    return resolve_contract_identity(
        segment_text=segment_text,
        anno=anno,
        predicted_contract_type=predicted_contract_type,
        detail_id=detail_id,
    )


def run_compat_pipeline(request: ParseRequest) -> ParseResult:
    """Build PositionRow values using the current legacy extraction flow."""
    if not request.text or request.text_quality == "no_text":
        return ParseResult(rows=[], pdf_call_title=None)

    pdf_call_title = extract_pdf_call_title(request.text)
    preprocessed = preprocess_text(request.text)
    segment_spans = segment_preprocessed(preprocessed)
    if not segment_spans:
        return ParseResult(rows=[], pdf_call_title=pdf_call_title)
    classifications = classify_segments(segment_spans)
    rows: list[PositionRow] = []
    diagnostics = EventCollector()

    for i, span in enumerate(segment_spans):
        seg = span.text
        identity = _resolve_identity(
            segment_text=seg,
            anno=request.anno,
            predicted_contract_type=classifications[i].contract_type,
            detail_id=request.detail_id,
        )
        _record_execution_events(
            diagnostics=diagnostics,
            detail_id=request.detail_id,
            result=identity.contract_type_result,
            field_name="contract_type",
            source_line_start=span.source_line_start,
            source_line_end=span.source_line_end,
        )
        _record_execution_events(
            diagnostics=diagnostics,
            detail_id=request.detail_id,
            result=identity.contract_subtype_result,
            field_name="contract_subtype",
            source_line_start=span.source_line_start,
            source_line_end=span.source_line_end,
        )
        dur_months, dur_raw, dur_ev = extract_duration(seg)
        income = extract_income(seg)
        section_resolved = resolve_section(
            segment_text=seg,
            detail_id=request.detail_id,
            anno=request.anno,
            contract_type=identity.contract_type,
        )
        _record_execution_events(
            diagnostics=diagnostics,
            detail_id=request.detail_id,
            result=section_resolved.execution_result,
            field_name="section_structure_department",
            source_line_start=span.source_line_start,
            source_line_end=span.source_line_end,
        )

        row = PositionRow(
            detail_id=request.detail_id,
            position_row_index=i,
            text_quality=request.text_quality,
            contract_type=identity.contract_type,
            contract_type_raw=identity.contract_type_raw,
            contract_type_evidence=identity.contract_type_evidence,
            contract_subtype=identity.contract_subtype,
            contract_subtype_raw=identity.contract_subtype_raw,
            contract_subtype_evidence=identity.contract_subtype_evidence,
            duration_months=dur_months,
            duration_raw=dur_raw,
            duration_evidence=dur_ev,
            section_structure_department=section_resolved.value,
            section_evidence=section_resolved.evidence,
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
        row.parse_confidence = score_confidence(row, request.text_quality).value
        rows.append(row)

    _ = diagnostics.snapshot()
    return ParseResult(rows=rows, pdf_call_title=pdf_call_title)
