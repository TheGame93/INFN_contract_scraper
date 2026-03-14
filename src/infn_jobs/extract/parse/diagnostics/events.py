"""Diagnostic event model for parser tracing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParseEvent:
    """Represent one parser diagnostic event."""

    stage: str
    message: str
    detail_id: str | None = None
    source_line_start: int | None = None
    source_line_end: int | None = None
    event_type: str = "info"
    field_name: str | None = None
    rule_id: str | None = None
    reason_code: str | None = None
    candidate_value: object | None = None
    priority_tier: str | None = None
    resolution_policy: str | None = None
