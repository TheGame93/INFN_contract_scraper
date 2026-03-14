"""Build deterministic parser review artifacts for one parse case."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.core.classification import classify_segments
from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed
from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.diagnostics.render import render_events
from infn_jobs.extract.parse.fields.metadata import extract_pdf_call_title
from infn_jobs.extract.parse.rules.contract_identity import resolve_contract_identity
from infn_jobs.extract.parse.rules.duration import resolve_duration
from infn_jobs.extract.parse.rules.income import resolve_income
from infn_jobs.extract.parse.rules.models import ExecutionResult
from infn_jobs.extract.parse.rules.section import resolve_section


@dataclass(frozen=True)
class SegmentReview:
    """Deterministic parse-review artifacts for one segment."""

    segment_index: int
    source_line_start: int | None
    source_line_end: int | None
    predicted_contract_type: str | None
    predicted_confidence: float
    contract_type: str | None
    contract_subtype: str | None
    duration_months: int | None
    section_structure_department: str | None
    gross_income_yearly_eur: float | None
    winner_rule_ids: dict[str, str | None]
    evidence: dict[str, str | None]


@dataclass(frozen=True)
class ParseReviewReport:
    """Deterministic parse-review payload for one detail_id case."""

    detail_id: str
    anno: int | None
    text_quality: str
    pdf_call_title: str | None
    segments: tuple[SegmentReview, ...]
    diagnostics_rendered: str


def build_review_report(
    *,
    text: str,
    detail_id: str,
    text_quality: str,
    anno: int | None,
) -> ParseReviewReport:
    """Return deterministic parse-review artifacts from one mutool text payload."""
    if not text:
        return ParseReviewReport(
            detail_id=detail_id,
            anno=anno,
            text_quality=text_quality,
            pdf_call_title=None,
            segments=(),
            diagnostics_rendered="",
        )

    pdf_call_title = extract_pdf_call_title(text)
    spans = segment_preprocessed(preprocess_text(text))
    classifications = classify_segments(spans)
    diagnostics = EventCollector()
    segments: list[SegmentReview] = []

    for index, span in enumerate(spans):
        identity = resolve_contract_identity(
            segment_text=span.text,
            anno=anno,
            predicted_contract_type=classifications[index].contract_type,
            detail_id=detail_id,
        )
        duration = resolve_duration(
            segment_text=span.text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )
        income = resolve_income(
            segment_text=span.text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )
        section = resolve_section(
            segment_text=span.text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )

        _record_events(
            diagnostics,
            detail_id,
            identity.contract_type_result,
            "contract_type",
            span,
        )
        _record_events(
            diagnostics,
            detail_id,
            identity.contract_subtype_result,
            "contract_subtype",
            span,
        )
        _record_events(diagnostics, detail_id, duration.execution_result, "duration", span)
        for field_name, result in income.execution_results.items():
            _record_events(diagnostics, detail_id, result, field_name, span)
        _record_events(
            diagnostics,
            detail_id,
            section.execution_result,
            "section_structure_department",
            span,
        )

        segments.append(
            SegmentReview(
                segment_index=index,
                source_line_start=span.source_line_start,
                source_line_end=span.source_line_end,
                predicted_contract_type=classifications[index].contract_type,
                predicted_confidence=classifications[index].confidence,
                contract_type=identity.contract_type,
                contract_subtype=identity.contract_subtype,
                duration_months=duration.duration_months,
                section_structure_department=section.value,
                gross_income_yearly_eur=income.values["gross_income_yearly_eur"],  # type: ignore[assignment]
                winner_rule_ids={
                    "contract_type": _winner_rule_id(identity.contract_type_result),
                    "contract_subtype": _winner_rule_id(identity.contract_subtype_result),
                    "duration": _winner_rule_id(duration.execution_result),
                    "gross_income_yearly_eur": _winner_rule_id(
                        income.execution_results["gross_income_yearly_eur"]
                    ),
                    "section_structure_department": _winner_rule_id(section.execution_result),
                },
                evidence={
                    "contract_type": identity.contract_type_evidence,
                    "contract_subtype": identity.contract_subtype_evidence,
                    "duration": duration.evidence,
                    "gross_income": income.values["gross_income_evidence"],  # type: ignore[dict-item]
                    "section": section.evidence,
                },
            )
        )

    return ParseReviewReport(
        detail_id=detail_id,
        anno=anno,
        text_quality=text_quality,
        pdf_call_title=pdf_call_title,
        segments=tuple(segments),
        diagnostics_rendered=render_events(diagnostics.snapshot()),
    )


def render_review_report(report: ParseReviewReport) -> str:
    """Render one deterministic text block for parse-review artifacts."""
    lines = [
        f"detail_id={report.detail_id}",
        f"anno={report.anno if report.anno is not None else '-'}",
        f"text_quality={report.text_quality}",
        f"pdf_call_title={report.pdf_call_title or '-'}",
        f"segment_count={len(report.segments)}",
    ]
    for segment in report.segments:
        lines.append(
            (
                "segment[{idx}]|lines={start}-{end}|predicted={pred}|pred_conf={conf:.4f}|"
                "contract_type={ctype}|contract_subtype={subtype}|duration_months={duration}|"
                "gross_income_yearly_eur={gross}|section={section}|rules={rules}"
            ).format(
                idx=segment.segment_index,
                start=segment.source_line_start if segment.source_line_start is not None else "-",
                end=segment.source_line_end if segment.source_line_end is not None else "-",
                pred=segment.predicted_contract_type or "-",
                conf=segment.predicted_confidence,
                ctype=segment.contract_type or "-",
                subtype=segment.contract_subtype or "-",
                duration=segment.duration_months if segment.duration_months is not None else "-",
                gross=(
                    f"{segment.gross_income_yearly_eur:.2f}"
                    if segment.gross_income_yearly_eur is not None
                    else "-"
                ),
                section=segment.section_structure_department or "-",
                rules=",".join(
                    f"{key}:{value or '-'}"
                    for key, value in sorted(segment.winner_rule_ids.items())
                ),
            )
        )
    lines.append("diagnostics:")
    lines.append(report.diagnostics_rendered or "-")
    return "\n".join(lines)


def _winner_rule_id(result: ExecutionResult) -> str | None:
    """Return winner rule_id for one rule execution result."""
    if result.winner is None:
        return None
    return result.winner.rule_id


def _record_events(
    diagnostics: EventCollector,
    detail_id: str,
    result: ExecutionResult,
    field_name: str,
    span,
) -> None:
    """Record winner and rejected events from one execution result."""
    for rejected in result.rejected:
        diagnostics.record_rejected(
            detail_id=detail_id,
            rejected=rejected,
            source_line_start=span.source_line_start,
            source_line_end=span.source_line_end,
        )
    if result.winner is not None:
        diagnostics.record_winner(
            detail_id=detail_id,
            field_name=field_name,
            candidate=result.winner,
            source_line_start=span.source_line_start,
            source_line_end=span.source_line_end,
        )
