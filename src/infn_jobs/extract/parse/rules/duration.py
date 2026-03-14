"""Rule adapters for duration extraction and resolution."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.core.conflict_resolution import merge_execution_results
from infn_jobs.extract.parse.rules import duration_helpers
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext, RuleDefinition


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


def _duration_primary_rules() -> tuple[RuleDefinition, ...]:
    """Return primary duration rules with labeled evidence precedence."""
    return (
        RuleDefinition(
            rule_id="duration.primary.10.labeled_numeric",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_labeled_numeric(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.20.labeled_one_month",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_labeled_one_month(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.30.labeled_triennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_labeled_triennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.40.labeled_biennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_labeled_biennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.50.labeled_annuale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_labeled_annuale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_fallback_rules() -> tuple[RuleDefinition, ...]:
    """Return fallback duration rules for bare word expressions."""
    return (
        RuleDefinition(
            rule_id="duration.fallback.10.bare_triennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_bare_triennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.20.bare_biennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_bare_biennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.30.bare_annuale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_bare_annuale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_guard_rules() -> tuple[RuleDefinition, ...]:
    """Return guard-tier duration rules for constrained numeric fallback."""
    return (
        RuleDefinition(
            rule_id="duration.guard.10.numeric_context",
            field_name="duration",
            priority_tier="guard",
            guards=(_has_duration_context,),
            transformer=lambda context: _to_duration_value(
                duration_helpers.extract_numeric_guarded(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


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
            execute_rules(_duration_primary_rules(), context),
            execute_rules(_duration_fallback_rules(), context),
            execute_rules(_duration_guard_rules(), context),
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
