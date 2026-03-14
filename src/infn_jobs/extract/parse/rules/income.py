"""Rule adapters for income and cost field extraction."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.rules import income_helpers
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.income_rule_specs import INCOME_FIELD_RULE_SPECS
from infn_jobs.extract.parse.rules.models import (
    ExecutionResult,
    PriorityTier,
    RuleContext,
    RuleDefinition,
)


@dataclass(frozen=True)
class IncomeAmount:
    """One parsed EUR amount candidate plus its evidence line."""

    value: float
    evidence: str


@dataclass(frozen=True)
class IncomeResolution:
    """Resolved income fields and per-field execution traces."""

    values: dict[str, float | str | None]
    execution_results: dict[str, ExecutionResult]


def _to_income_amount(candidate: tuple[float, str] | None) -> IncomeAmount | None:
    """Convert helper tuple output into a typed income candidate."""
    if candidate is None:
        return None
    value, evidence = candidate
    return IncomeAmount(value=value, evidence=evidence)


def _candidate(
    context: RuleContext,
    *,
    label_re,
    require_total: bool = False,
    require_yearly: bool = False,
    require_monthly: bool = False,
    require_no_qualifier: bool = False,
) -> IncomeAmount | None:
    """Resolve one candidate amount for a rule invocation."""
    return _to_income_amount(
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
            label_re=label_re,
            require_total=require_total,
            require_yearly=require_yearly,
            require_monthly=require_monthly,
            require_no_qualifier=require_no_qualifier,
        ),
        evidence_selector=lambda _context, value: value.evidence,
    )


def _rules_for_field(field_name: str) -> tuple[RuleDefinition, ...]:
    """Return deterministic rule set for one income field."""
    if field_name not in INCOME_FIELD_RULE_SPECS:
        raise ValueError(f"Unsupported income field: {field_name}")
    return tuple(
        _make_rule(field_name=field_name, **kwargs)
        for kwargs in INCOME_FIELD_RULE_SPECS[field_name]
    )


def _resolve_field(
    field_name: str,
    context: RuleContext,
) -> tuple[float | None, str | None, ExecutionResult]:
    """Resolve one income field via deterministic rules."""
    result = execute_rules(_rules_for_field(field_name), context)
    winner = result.winner
    if winner is None or not isinstance(winner.value, IncomeAmount):
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


def resolve_income(
    *,
    segment_text: str,
    detail_id: str = "",
    anno: int | None = None,
    contract_type: str | None = None,
) -> IncomeResolution:
    """Resolve all income fields through rule-driven per-field adapters."""
    context = RuleContext(
        segment_text=segment_text,
        detail_id=detail_id,
        anno=anno,
        contract_type=contract_type,
    )
    values: dict[str, float | str | None] = {
        "institute_cost_total_eur": None,
        "institute_cost_yearly_eur": None,
        "gross_income_total_eur": None,
        "gross_income_yearly_eur": None,
        "net_income_total_eur": None,
        "net_income_yearly_eur": None,
        "net_income_monthly_eur": None,
        "institute_cost_evidence": None,
        "gross_income_evidence": None,
        "net_income_evidence": None,
    }
    execution_results: dict[str, ExecutionResult] = {}

    for field_name in (
        "institute_cost_total_eur",
        "institute_cost_yearly_eur",
        "gross_income_total_eur",
        "gross_income_yearly_eur",
        "net_income_total_eur",
        "net_income_yearly_eur",
        "net_income_monthly_eur",
    ):
        amount, evidence, result = _resolve_field(field_name, context)
        values[field_name] = amount
        values[f"{field_name}_evidence"] = evidence
        execution_results[field_name] = result

    values["institute_cost_evidence"] = _pick_group_evidence(
        values,
        total_key="institute_cost_total_eur",
        yearly_key="institute_cost_yearly_eur",
    )
    values["gross_income_evidence"] = _pick_group_evidence(
        values,
        total_key="gross_income_total_eur",
        yearly_key="gross_income_yearly_eur",
    )
    values["net_income_evidence"] = _pick_group_evidence(
        values,
        monthly_key="net_income_monthly_eur",
        total_key="net_income_total_eur",
        yearly_key="net_income_yearly_eur",
    )

    return IncomeResolution(values=values, execution_results=execution_results)
