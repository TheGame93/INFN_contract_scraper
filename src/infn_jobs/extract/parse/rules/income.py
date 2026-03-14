"""Rule adapters for income and cost field extraction."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.rules.income_resolution_helpers import (
    _pick_group_evidence,
    _resolve_field,
)
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext


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
        amount, evidence, result = _resolve_field(
            field_name,
            context,
            to_income_amount=_to_income_amount,
        )
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
