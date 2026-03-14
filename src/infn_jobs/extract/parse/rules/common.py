"""Shared helpers for deterministic rule evaluation."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.models import PriorityTier, RuleContext, RuleDefinition

_TIER_RANK: dict[PriorityTier, int] = {
    "primary": 0,
    "fallback": 1,
    "guard": 2,
}


def priority_rank(tier: PriorityTier) -> int:
    """Return sortable priority rank for tier."""
    return _TIER_RANK[tier]


def contract_filter_matches(rule: RuleDefinition, context: RuleContext) -> bool:
    """Return True when contract filter allows this context."""
    if not rule.contract_filter:
        return True
    if context.contract_type is None:
        return False
    return context.contract_type in rule.contract_filter


def anno_filter_matches(rule: RuleDefinition, context: RuleContext) -> bool:
    """Return True when anno constraints allow this context."""
    if rule.anno_min is None and rule.anno_max is None:
        return True
    if context.anno is None:
        return False
    if rule.anno_min is not None and context.anno < rule.anno_min:
        return False
    if rule.anno_max is not None and context.anno > rule.anno_max:
        return False
    return True

