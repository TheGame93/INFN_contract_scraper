"""Tests for deterministic parser rule execution."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import RuleContext, RuleDefinition


def test_execute_rules_prefers_primary_over_fallback() -> None:
    """Primary-tier candidate should win over fallback-tier candidate."""
    context = RuleContext(segment_text="text", detail_id="d1", anno=2026)
    rules = (
        RuleDefinition(
            rule_id="fallback.rule",
            field_name="contract_type",
            priority_tier="fallback",
            transformer=lambda _ctx: "fallback-value",
        ),
        RuleDefinition(
            rule_id="primary.rule",
            field_name="contract_type",
            priority_tier="primary",
            transformer=lambda _ctx: "primary-value",
        ),
    )

    result = execute_rules(rules, context)
    assert result.winner is not None
    assert result.winner.rule_id == "primary.rule"
    assert result.winner.value == "primary-value"


def test_execute_rules_tie_breaks_by_rule_id() -> None:
    """Same-tier candidates should resolve deterministically by rule_id."""
    context = RuleContext(segment_text="text", detail_id="d1", anno=2026)
    rules = (
        RuleDefinition(
            rule_id="rule.zeta",
            field_name="contract_type",
            priority_tier="primary",
            transformer=lambda _ctx: "zeta",
        ),
        RuleDefinition(
            rule_id="rule.alpha",
            field_name="contract_type",
            priority_tier="primary",
            transformer=lambda _ctx: "alpha",
        ),
    )

    result = execute_rules(rules, context)
    assert result.winner is not None
    assert result.winner.rule_id == "rule.alpha"
    assert result.winner.value == "alpha"


def test_execute_rules_rejection_reason_codes() -> None:
    """Executor should emit explicit rejection reason codes."""
    context = RuleContext(
        segment_text="text",
        detail_id="d1",
        anno=2020,
        contract_type="Borsa di studio",
    )
    rules = (
        RuleDefinition(
            rule_id="reject.trigger",
            field_name="x",
            priority_tier="primary",
            transformer=lambda _ctx: "x",
            trigger=lambda _ctx: False,
        ),
        RuleDefinition(
            rule_id="reject.guard",
            field_name="x",
            priority_tier="primary",
            transformer=lambda _ctx: "x",
            guards=(lambda _ctx: False,),
        ),
        RuleDefinition(
            rule_id="reject.contract",
            field_name="x",
            priority_tier="primary",
            transformer=lambda _ctx: "x",
            contract_filter=("Assegno di ricerca",),
        ),
        RuleDefinition(
            rule_id="reject.era",
            field_name="x",
            priority_tier="primary",
            transformer=lambda _ctx: "x",
            anno_min=2022,
        ),
        RuleDefinition(
            rule_id="reject.none",
            field_name="x",
            priority_tier="primary",
            transformer=lambda _ctx: None,
        ),
    )

    result = execute_rules(rules, context)
    assert result.winner is None
    assert [item.reason_code for item in result.rejected] == [
        "trigger_false",
        "guard_blocked",
        "contract_mismatch",
        "era_mismatch",
        "no_value",
    ]

