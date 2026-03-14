"""Collector utility for parser diagnostic events."""

from __future__ import annotations

from infn_jobs.extract.parse.diagnostics.events import ParseEvent


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

