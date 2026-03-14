"""Internal helpers shared by review-mode diagnostics rendering and trace collection."""

from __future__ import annotations

from infn_jobs.extract.parse.core.execution_shared import _ExecutedSegment
from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.rules.models import ExecutionResult


def _winner_rule_id(result: ExecutionResult) -> str | None:
    """Return winner rule_id for one rule execution result."""
    if result.winner is None:
        return None
    return result.winner.rule_id


def _segment_winner_rule_ids(segment: _ExecutedSegment) -> dict[str, str | None]:
    """Return deterministic winner rule IDs for one reviewed segment."""
    return {
        "contract_type": _winner_rule_id(segment.identity.contract_type_result),
        "contract_subtype": _winner_rule_id(segment.identity.contract_subtype_result),
        "duration": _winner_rule_id(segment.duration.execution_result),
        "gross_income_yearly_eur": _winner_rule_id(
            segment.income.execution_results["gross_income_yearly_eur"]
        ),
        "section_structure_department": _winner_rule_id(segment.section.execution_result),
    }


def _segment_evidence(segment: _ExecutedSegment) -> dict[str, str | None]:
    """Return deterministic evidence snippets for one reviewed segment."""
    return {
        "contract_type": segment.identity.contract_type_evidence,
        "contract_subtype": segment.identity.contract_subtype_evidence,
        "duration": segment.duration.evidence,
        "gross_income": segment.income.values["gross_income_evidence"],  # type: ignore[dict-item]
        "section": segment.section.evidence,
    }


def _record_events(
    *,
    diagnostics: EventCollector,
    detail_id: str,
    result: ExecutionResult,
    field_name: str,
    source_line_start: int | None,
    source_line_end: int | None,
) -> None:
    """Record winner and rejected events from one execution result."""
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


def _record_segment_events(
    *,
    diagnostics: EventCollector,
    detail_id: str,
    segment: _ExecutedSegment,
) -> None:
    """Record all rule execution events for one executed parse segment."""
    _record_events(
        diagnostics=diagnostics,
        detail_id=detail_id,
        result=segment.identity.contract_type_result,
        field_name="contract_type",
        source_line_start=segment.source_line_start,
        source_line_end=segment.source_line_end,
    )
    _record_events(
        diagnostics=diagnostics,
        detail_id=detail_id,
        result=segment.identity.contract_subtype_result,
        field_name="contract_subtype",
        source_line_start=segment.source_line_start,
        source_line_end=segment.source_line_end,
    )
    _record_events(
        diagnostics=diagnostics,
        detail_id=detail_id,
        result=segment.duration.execution_result,
        field_name="duration",
        source_line_start=segment.source_line_start,
        source_line_end=segment.source_line_end,
    )
    for field_name, result in segment.income.execution_results.items():
        _record_events(
            diagnostics=diagnostics,
            detail_id=detail_id,
            result=result,
            field_name=field_name,
            source_line_start=segment.source_line_start,
            source_line_end=segment.source_line_end,
        )
    _record_events(
        diagnostics=diagnostics,
        detail_id=detail_id,
        result=segment.section.execution_result,
        field_name="section_structure_department",
        source_line_start=segment.source_line_start,
        source_line_end=segment.source_line_end,
    )
