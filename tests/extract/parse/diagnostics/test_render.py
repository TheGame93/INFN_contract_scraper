"""Tests for diagnostics renderer."""

from infn_jobs.extract.parse.diagnostics.events import ParseEvent
from infn_jobs.extract.parse.diagnostics.render import render_events


def test_render_events_outputs_deterministic_pipe_lines() -> None:
    """Renderer should emit stable line format for diagnostics events."""
    events = (
        ParseEvent(
            stage="rule_executor",
            message="winner selected",
            detail_id="d1",
            event_type="winner",
            field_name="contract_type",
            rule_id="rule.primary",
            candidate_value="Borsa di studio",
            priority_tier="primary",
        ),
        ParseEvent(
            stage="rule_executor",
            message="candidate rejected",
            detail_id="d1",
            event_type="rejected",
            field_name="contract_type",
            rule_id="rule.fallback",
            reason_code="no_value",
        ),
    )

    rendered = render_events(events)
    assert rendered.splitlines() == [
        "rule_executor|winner|contract_type|rule.primary|-|Borsa di studio",
        "rule_executor|rejected|contract_type|rule.fallback|no_value|-",
    ]

