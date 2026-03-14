"""Internal helper functions for income rule resolution."""

from __future__ import annotations

from collections.abc import Callable

from infn_jobs.extract.parse.rules import income_helpers
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.income_rule_specs import INCOME_FIELD_RULE_SPECS
from infn_jobs.extract.parse.rules.models import (
    ExecutionResult,
    PriorityTier,
    RuleContext,
    RuleDefinition,
)

_ToIncomeAmount = Callable[[tuple[float, str] | None], object | None]


def _candidate(
    context: RuleContext,
    *,
    to_income_amount: _ToIncomeAmount,
    label_re,
    require_total: bool = False,
    require_yearly: bool = False,
    require_monthly: bool = False,
    require_no_qualifier: bool = False,
):
    """Resolve one candidate amount for a rule invocation."""
    return to_income_amount(
        income_helpers.find_amount(
            segment_text=context.segment_text,
            label_re=label_re,
            require_total=require_total,
            require_yearly=require_yearly,
            require_monthly=require_monthly,
            require_no_qualifier=require_no_qualifier,
        )
    )


def _make_rule(
    *,
    to_income_amount: _ToIncomeAmount,
    rule_id: str,
    field_name: str,
    tier: PriorityTier,
    label_re,
    require_total: bool = False,
    require_yearly: bool = False,
    require_monthly: bool = False,
    require_no_qualifier: bool = False,
) -> RuleDefinition:
    """Return one deterministic income rule definition."""
    return RuleDefinition(
        rule_id=rule_id,
        field_name=field_name,
        priority_tier=tier,
        transformer=lambda context: _candidate(
            context,
            to_income_amount=to_income_amount,
            label_re=label_re,
            require_total=require_total,
            require_yearly=require_yearly,
            require_monthly=require_monthly,
            require_no_qualifier=require_no_qualifier,
        ),
        evidence_selector=lambda _context, value: value.evidence,
    )


def _rules_for_field(
    field_name: str,
    *,
    to_income_amount: _ToIncomeAmount,
) -> tuple[RuleDefinition, ...]:
    """Return deterministic rule set for one income field."""
    if field_name not in INCOME_FIELD_RULE_SPECS:
        raise ValueError(f"Unsupported income field: {field_name}")
    return tuple(
        _make_rule(field_name=field_name, to_income_amount=to_income_amount, **kwargs)
        for kwargs in INCOME_FIELD_RULE_SPECS[field_name]
    )


def _resolve_field(
    field_name: str,
    context: RuleContext,
    *,
    to_income_amount: _ToIncomeAmount,
) -> tuple[float | None, str | None, ExecutionResult]:
    """Resolve one income field via deterministic rules."""
    result = execute_rules(
        _rules_for_field(field_name, to_income_amount=to_income_amount),
        context,
    )
    winner = result.winner
    if winner is None:
        return None, None, result
    if not hasattr(winner.value, "value") or not hasattr(winner.value, "evidence"):
        return None, None, result
    return winner.value.value, winner.value.evidence, result


def _pick_group_evidence(
    values: dict[str, float | str | None],
    *,
    monthly_key: str | None = None,
    total_key: str | None = None,
    yearly_key: str | None = None,
) -> str | None:
    """Return deterministic group evidence by qualifier preference."""
    evidence_lookup = {
        "monthly": f"{monthly_key}_evidence" if monthly_key else None,
        "total": f"{total_key}_evidence" if total_key else None,
        "yearly": f"{yearly_key}_evidence" if yearly_key else None,
    }
    for order_key in ("monthly", "total", "yearly"):
        key = evidence_lookup[order_key]
        if key is None:
            continue
        evidence = values.get(key)
        if isinstance(evidence, str):
            return evidence
    return None
