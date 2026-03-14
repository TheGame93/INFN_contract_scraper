"""Internal rule builders for duration extraction resolution."""

from __future__ import annotations

from collections.abc import Callable

from infn_jobs.extract.parse.rules import duration_helpers
from infn_jobs.extract.parse.rules.models import RuleContext, RuleDefinition

_DurationConverter = Callable[[tuple[int, str, str] | None], object | None]


def _duration_primary_rules(
    to_duration_value: _DurationConverter,
) -> tuple[RuleDefinition, ...]:
    """Return primary duration rules with labeled evidence precedence."""
    return (
        RuleDefinition(
            rule_id="duration.primary.10.labeled_numeric",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_labeled_numeric(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.20.labeled_one_month",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_labeled_one_month(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.30.labeled_triennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_labeled_triennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.40.labeled_biennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_labeled_biennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.50.labeled_annuale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_labeled_annuale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_fallback_rules(
    *,
    to_duration_value: _DurationConverter,
    has_duration_context: Callable[[RuleContext], bool],
) -> tuple[RuleDefinition, ...]:
    """Return fallback duration rules for bare word expressions."""
    return (
        RuleDefinition(
            rule_id="duration.fallback.10.bare_triennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(has_duration_context,),
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_bare_triennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.20.bare_biennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(has_duration_context,),
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_bare_biennale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.30.bare_annuale",
            field_name="duration",
            priority_tier="fallback",
            guards=(has_duration_context,),
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_bare_annuale(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_guard_rules(
    *,
    to_duration_value: _DurationConverter,
    has_duration_context: Callable[[RuleContext], bool],
) -> tuple[RuleDefinition, ...]:
    """Return guard-tier duration rules for constrained numeric fallback."""
    return (
        RuleDefinition(
            rule_id="duration.guard.10.numeric_context",
            field_name="duration",
            priority_tier="guard",
            guards=(has_duration_context,),
            transformer=lambda context: to_duration_value(
                duration_helpers.extract_numeric_guarded(context.segment_text)
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )
