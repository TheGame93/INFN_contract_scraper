"""Compatibility orchestrator for parser execution."""

from __future__ import annotations

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.core.classification import classify_segments
from infn_jobs.extract.parse.core.models import ParseRequest, ParseResult
from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed
from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.fields.confidence import score_confidence
from infn_jobs.extract.parse.fields.contract_type import extract_contract_type
from infn_jobs.extract.parse.fields.duration import extract_duration
from infn_jobs.extract.parse.fields.income import extract_income
from infn_jobs.extract.parse.fields.metadata import (
    extract_pdf_call_title,
    extract_section_department,
)
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import RuleContext, RuleDefinition


def _fallback_contract_transformer(context: RuleContext) -> object | None:
    """Return predicted contract type from context metadata."""
    return context.metadata.get("predicted_contract_type")


def _fallback_contract_evidence(context: RuleContext, _value: object) -> str | None:
    """Return first segment line as fallback contract evidence."""
    lines = context.segment_text.splitlines()
    return lines[0] if lines else None


_CONTRACT_TYPE_FALLBACK_RULES: tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="fallback.classification.contract_type",
        field_name="contract_type",
        priority_tier="fallback",
        transformer=_fallback_contract_transformer,
        evidence_selector=_fallback_contract_evidence,
    ),
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
        ct = extract_contract_type(seg, request.anno)
        fallback_result = execute_rules(
            _CONTRACT_TYPE_FALLBACK_RULES,
            RuleContext(
                segment_text=seg,
                detail_id=request.detail_id,
                anno=request.anno,
                contract_type=ct["contract_type"],
                metadata={"predicted_contract_type": classifications[i].contract_type},
            ),
        )
        for rejected in fallback_result.rejected:
            diagnostics.record_rejected(
                detail_id=request.detail_id,
                rejected=rejected,
                source_line_start=span.source_line_start,
                source_line_end=span.source_line_end,
            )
        if fallback_result.winner is not None:
            diagnostics.record_winner(
                detail_id=request.detail_id,
                field_name="contract_type",
                candidate=fallback_result.winner,
                source_line_start=span.source_line_start,
                source_line_end=span.source_line_end,
            )
        if ct["contract_type"] is None and fallback_result.winner is not None:
            winner_value = str(fallback_result.winner.value)
            ct["contract_type"] = winner_value
            ct["contract_type_raw"] = winner_value
            ct["contract_type_evidence"] = fallback_result.winner.evidence

        dur_months, dur_raw, dur_ev = extract_duration(seg)
        income = extract_income(seg)
        section, section_ev = extract_section_department(seg)

        row = PositionRow(
            detail_id=request.detail_id,
            position_row_index=i,
            text_quality=request.text_quality,
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
        row.parse_confidence = score_confidence(row, request.text_quality).value
        rows.append(row)

    _ = diagnostics.snapshot()
    return ParseResult(rows=rows, pdf_call_title=pdf_call_title)
