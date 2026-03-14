"""Collector utility for parser diagnostic events."""

from __future__ import annotations

from infn_jobs.extract.parse.diagnostics.events import ParseEvent
from infn_jobs.extract.parse.rules.models import RejectedCandidate, RuleCandidate


class EventCollector:
    """Collect parser events in insertion order."""

    def __init__(self) -> None:
        """Initialize an empty event collector."""
        self._events: list[ParseEvent] = []

    def record(self, event: ParseEvent) -> None:
        """Store one parser event."""
        self._events.append(event)

    def snapshot(self) -> tuple[ParseEvent, ...]:
        """Return an immutable snapshot of recorded events."""
        return tuple(self._events)

    def record_winner(
        self,
        *,
        detail_id: str,
        field_name: str,
        candidate: RuleCandidate,
        source_line_start: int | None = None,
        source_line_end: int | None = None,
    ) -> None:
        """Record one winner event from rule execution."""
        self.record(
            ParseEvent(
                stage="rule_executor",
                message="winner selected",
                detail_id=detail_id,
                source_line_start=source_line_start,
                source_line_end=source_line_end,
                event_type="winner",
                field_name=field_name,
                rule_id=candidate.rule_id,
                candidate_value=candidate.value,
                priority_tier=candidate.priority_tier,
                resolution_policy="tier_then_rule_id",
            )
        )

    def record_rejected(
        self,
        *,
        detail_id: str,
        rejected: RejectedCandidate,
        source_line_start: int | None = None,
        source_line_end: int | None = None,
    ) -> None:
        """Record one rejected-candidate event from rule execution."""
        self.record(
            ParseEvent(
                stage="rule_executor",
                message="candidate rejected",
                detail_id=detail_id,
                source_line_start=source_line_start,
                source_line_end=source_line_end,
                event_type="rejected",
                field_name=rejected.field_name,
                rule_id=rejected.rule_id,
                reason_code=rejected.reason_code,
                resolution_policy="tier_then_rule_id",
            )
        )
