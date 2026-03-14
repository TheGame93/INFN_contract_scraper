"""Build deterministic parser review artifacts for one parse case."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.core.execution_shared import _execute_segments
from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.diagnostics.render import render_events
from infn_jobs.extract.parse.diagnostics.review_mode_helpers import (
    _record_segment_events,
    _segment_evidence,
    _segment_winner_rule_ids,
)


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

    execution = _execute_segments(text=text, detail_id=detail_id, anno=anno)
    diagnostics = EventCollector()
    segments: list[SegmentReview] = []

    for segment in execution.segments:
        _record_segment_events(diagnostics=diagnostics, detail_id=detail_id, segment=segment)
        segments.append(
            SegmentReview(
                segment_index=segment.segment_index,
                source_line_start=segment.source_line_start,
                source_line_end=segment.source_line_end,
                predicted_contract_type=segment.predicted_contract_type,
                predicted_confidence=segment.predicted_confidence,
                contract_type=segment.identity.contract_type,
                contract_subtype=segment.identity.contract_subtype,
                duration_months=segment.duration.duration_months,
                section_structure_department=segment.section.value,
                gross_income_yearly_eur=segment.income.values["gross_income_yearly_eur"],  # type: ignore[assignment]
                winner_rule_ids=_segment_winner_rule_ids(segment),
                evidence=_segment_evidence(segment),
            )
        )

    return ParseReviewReport(
        detail_id=detail_id,
        anno=anno,
        text_quality=text_quality,
        pdf_call_title=execution.pdf_call_title,
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
