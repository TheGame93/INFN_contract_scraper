"""Rule adapters for duration extraction and resolution."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.core.conflict_resolution import merge_execution_results
from infn_jobs.extract.parse.rules import duration_helpers
from infn_jobs.extract.parse.rules.duration_rule_builders import (
    _duration_fallback_rules,
    _duration_guard_rules,
    _duration_primary_rules,
)
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext


@dataclass(frozen=True)
class DurationValue:
    """One duration candidate value plus its raw snippet and evidence line."""

    months: int
    raw: str
    evidence: str


@dataclass(frozen=True)
class DurationResolution:
    """Resolved duration fields plus underlying rule execution trace."""

    duration_months: int | None
    duration_raw: str | None
    evidence: str | None
    execution_result: ExecutionResult


def _has_duration_context(context: RuleContext) -> bool:
    """Return True when segment includes duration-like context words."""
    return duration_helpers.has_duration_context(context.segment_text)


def _to_duration_value(candidate: tuple[int, str, str] | None) -> DurationValue | None:
    """Convert helper tuple output into a typed duration candidate."""
    if candidate is None:
        return None
    months, raw, evidence = candidate
    return DurationValue(months=months, raw=raw, evidence=evidence)


def resolve_duration(
    *,
    segment_text: str,
    detail_id: str = "",
    anno: int | None = None,
    contract_type: str | None = None,
) -> DurationResolution:
    """Resolve duration fields via primary/fallback/guard rule groups."""
    context = RuleContext(
        segment_text=segment_text,
        detail_id=detail_id,
        anno=anno,
        contract_type=contract_type,
    )
    merged = merge_execution_results(
        (
            execute_rules(_duration_primary_rules(_to_duration_value), context),
            execute_rules(
                _duration_fallback_rules(
                    to_duration_value=_to_duration_value,
                    has_duration_context=_has_duration_context,
                ),
                context,
            ),
            execute_rules(
                _duration_guard_rules(
                    to_duration_value=_to_duration_value,
                    has_duration_context=_has_duration_context,
                ),
                context,
            ),
        )
    )

    winner = merged.winner
    if winner is None or not isinstance(winner.value, DurationValue):
        return DurationResolution(
            duration_months=None,
            duration_raw=None,
            evidence=None,
            execution_result=merged,
        )
    return DurationResolution(
        duration_months=winner.value.months,
        duration_raw=winner.value.raw,
        evidence=winner.value.evidence,
        execution_result=merged,
    )
