"""Deterministic execution engine for rule candidates."""

from __future__ import annotations

from infn_jobs.extract.parse.core.conflict_resolution import choose_winner
from infn_jobs.extract.parse.rules.common import (
    anno_filter_matches,
    contract_filter_matches,
)
from infn_jobs.extract.parse.rules.models import (
    ExecutionResult,
    RejectedCandidate,
    RuleCandidate,
    RuleContext,
    RuleDefinition,
)


def execute_rules(
    rules: tuple[RuleDefinition, ...],
    context: RuleContext,
) -> ExecutionResult:
    """Execute rules and return winner/candidates/rejected trace."""
    candidates: list[RuleCandidate] = []
    rejected: list[RejectedCandidate] = []

    for rule in rules:
        if rule.trigger is not None and not rule.trigger(context):
            rejected.append(
                RejectedCandidate(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    reason_code="trigger_false",
                )
            )
            continue

        if rule.guards and not all(guard(context) for guard in rule.guards):
            rejected.append(
                RejectedCandidate(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    reason_code="guard_blocked",
                )
            )
            continue

        if not contract_filter_matches(rule, context):
            rejected.append(
                RejectedCandidate(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    reason_code="contract_mismatch",
                )
            )
            continue

        if not anno_filter_matches(rule, context):
            rejected.append(
                RejectedCandidate(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    reason_code="era_mismatch",
                )
            )
            continue

        value = rule.transformer(context)
        if value is None:
            rejected.append(
                RejectedCandidate(
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    reason_code="no_value",
                )
            )
            continue

        evidence = (
            rule.evidence_selector(context, value)
            if rule.evidence_selector is not None
            else None
        )
        candidates.append(
            RuleCandidate(
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                value=value,
                evidence=evidence,
                priority_tier=rule.priority_tier,
            )
        )

    winner = choose_winner(tuple(candidates))
    return ExecutionResult(
        winner=winner,
        candidates=tuple(candidates),
        rejected=tuple(rejected),
    )
