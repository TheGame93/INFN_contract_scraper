"""Tests for parser diagnostics collector."""

from infn_jobs.extract.parse.diagnostics.collector import EventCollector
from infn_jobs.extract.parse.rules.models import RejectedCandidate, RuleCandidate


def test_event_collector_records_winner_and_rejected() -> None:
    """Collector should capture winner and rejected events in order."""
    collector = EventCollector()
    collector.record_winner(
        detail_id="d1",
        field_name="contract_type",
        candidate=RuleCandidate(
            rule_id="rule.primary",
            field_name="contract_type",
            value="Borsa di studio",
            evidence="BORSA DI STUDIO",
            priority_tier="primary",
        ),
        source_line_start=10,
        source_line_end=12,
    )
    collector.record_rejected(
        detail_id="d1",
        rejected=RejectedCandidate(
            rule_id="rule.fallback",
            field_name="contract_type",
            reason_code="no_value",
        ),
        source_line_start=10,
        source_line_end=12,
    )

    events = collector.snapshot()
    assert len(events) == 2
    assert events[0].event_type == "winner"
    assert events[0].rule_id == "rule.primary"
    assert events[0].candidate_value == "Borsa di studio"
    assert events[1].event_type == "rejected"
    assert events[1].rule_id == "rule.fallback"
    assert events[1].reason_code == "no_value"

