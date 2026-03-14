"""Render parser diagnostics into deterministic text output."""

from __future__ import annotations

from infn_jobs.extract.parse.diagnostics.events import ParseEvent


def render_events(events: tuple[ParseEvent, ...]) -> str:
    """Return one deterministic text block for diagnostics events."""
    lines: list[str] = []
    for event in events:
        lines.append(
            "|".join(
                [
                    event.stage,
                    event.event_type,
                    event.field_name or "-",
                    event.rule_id or "-",
                    event.reason_code or "-",
                    str(event.candidate_value) if event.candidate_value is not None else "-",
                ]
            )
        )
    return "\n".join(lines)

