"""Data models for rule-driven parser execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleCandidate:
    """One candidate value proposed by a parser rule."""

    rule_id: str
    field_name: str
    value: object
    evidence: str | None = None
    priority_tier: str = "primary"

