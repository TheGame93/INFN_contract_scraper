"""Tests for shared candidate conflict resolution policy."""

from infn_jobs.extract.parse.core.conflict_resolution import (
    candidate_sort_key,
    choose_winner,
    merge_execution_results,
)
from infn_jobs.extract.parse.rules.models import (
    ExecutionResult,
    RejectedCandidate,
    RuleCandidate,
)


def test_candidate_sort_key_orders_by_tier_then_rule_id() -> None:
    """Sort key should encode stable tier/rule precedence."""
    candidate = RuleCandidate(
        rule_id="rule.beta",
        field_name="duration",
        value=12,
        priority_tier="fallback",
    )
    assert candidate_sort_key(candidate) == (1, "rule.beta")


def test_choose_winner_prefers_primary_then_rule_id() -> None:
    """Winner selection should prefer primary tier and deterministic rule ordering."""
    winner = choose_winner(
        (
            RuleCandidate(
                rule_id="rule.zeta",
                field_name="duration",
                value=12,
                priority_tier="primary",
            ),
            RuleCandidate(
                rule_id="rule.alpha",
                field_name="duration",
                value=24,
                priority_tier="primary",
            ),
            RuleCandidate(
                rule_id="rule.fallback",
                field_name="duration",
                value=36,
                priority_tier="fallback",
            ),
        )
    )
    assert winner is not None
    assert winner.rule_id == "rule.alpha"
    assert winner.value == 24


def test_merge_execution_results_combines_trace_and_resolves_winner() -> None:
    """Merged results should preserve candidates/rejections and deterministic winner."""
    merged = merge_execution_results(
        (
            ExecutionResult(
                winner=None,
                candidates=(
                    RuleCandidate(
                        rule_id="rule.fallback",
                        field_name="duration",
                        value=24,
                        priority_tier="fallback",
                    ),
                ),
                rejected=(
                    RejectedCandidate(
                        rule_id="rule.guard",
                        field_name="duration",
                        reason_code="guard_blocked",
                    ),
                ),
            ),
            ExecutionResult(
                winner=None,
                candidates=(
                    RuleCandidate(
                        rule_id="rule.primary",
                        field_name="duration",
                        value=12,
                        priority_tier="primary",
                    ),
                ),
                rejected=(),
            ),
        )
    )
    assert merged.winner is not None
    assert merged.winner.rule_id == "rule.primary"
    assert len(merged.candidates) == 2
    assert len(merged.rejected) == 1
    assert merged.rejected[0].reason_code == "guard_blocked"
