"""Data models for rule-driven parser execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

PriorityTier = Literal["primary", "fallback", "guard"]
RejectReason = Literal[
    "trigger_false",
    "guard_blocked",
    "contract_mismatch",
    "era_mismatch",
    "no_value",
]


@dataclass(frozen=True)
class RuleContext:
    """Execution context passed to parser rules."""

    segment_text: str
    detail_id: str
    anno: int | None
    contract_type: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleDefinition:
    """Define one extraction rule and its evaluation constraints."""

    rule_id: str
    field_name: str
    priority_tier: PriorityTier
    transformer: Callable[[RuleContext], object | None]
    trigger: Callable[[RuleContext], bool] | None = None
    guards: tuple[Callable[[RuleContext], bool], ...] = ()
    contract_filter: tuple[str, ...] = ()
    anno_min: int | None = None
    anno_max: int | None = None
    evidence_selector: Callable[[RuleContext, object], str | None] | None = None


@dataclass(frozen=True)
class RuleCandidate:
    """One candidate value proposed by a parser rule."""

    rule_id: str
    field_name: str
    value: object
    evidence: str | None = None
    priority_tier: PriorityTier = "primary"


@dataclass(frozen=True)
class RejectedCandidate:
    """One rejected candidate decision emitted by the executor."""

    rule_id: str
    field_name: str
    reason_code: RejectReason


@dataclass(frozen=True)
class ExecutionResult:
    """Deterministic executor output for one field resolution."""

    winner: RuleCandidate | None
    candidates: tuple[RuleCandidate, ...]
    rejected: tuple[RejectedCandidate, ...]
