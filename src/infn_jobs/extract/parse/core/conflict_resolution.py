"""Shared deterministic conflict-resolution helpers for rule candidates."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.common import priority_rank
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleCandidate


def candidate_sort_key(candidate: RuleCandidate) -> tuple[int, str]:
    """Return a stable precedence key `(tier_rank, rule_id)` for one candidate."""
    return priority_rank(candidate.priority_tier), candidate.rule_id


def choose_winner(candidates: tuple[RuleCandidate, ...]) -> RuleCandidate | None:
    """Return deterministic winner candidate from a candidate set."""
    if not candidates:
        return None
    return min(candidates, key=candidate_sort_key)


def merge_execution_results(results: tuple[ExecutionResult, ...]) -> ExecutionResult:
    """Merge execution results and resolve one deterministic winner."""
    candidates = tuple(candidate for result in results for candidate in result.candidates)
    rejected = tuple(item for result in results for item in result.rejected)
    return ExecutionResult(
        winner=choose_winner(candidates),
        candidates=candidates,
        rejected=rejected,
    )
