"""Tests for rule-driven duration extraction."""

from infn_jobs.extract.parse.rules.duration import resolve_duration


def test_resolve_duration_prefers_primary_labeled_numeric() -> None:
    """Primary labeled numeric rule should win with deterministic evidence."""
    result = resolve_duration(segment_text="Durata: 24 mesi\n")
    assert result.duration_months == 24
    assert result.duration_raw == "24 mesi"
    assert result.evidence == "Durata: 24 mesi"
    assert result.execution_result.winner is not None
    assert result.execution_result.winner.rule_id == "duration.primary.10.labeled_numeric"


def test_resolve_duration_uses_fallback_for_bare_word_with_context() -> None:
    """Fallback bare-word rule should resolve contextual 'biennale' lines."""
    segment = "Incarico di ricerca biennale nell'ambito del progetto.\n"
    result = resolve_duration(segment_text=segment)
    assert result.duration_months == 24
    assert result.duration_raw == "biennale"
    assert result.execution_result.winner is not None
    assert result.execution_result.winner.priority_tier == "fallback"


def test_resolve_duration_blocks_false_positive_without_context() -> None:
    """Narrative lines without duration context should not emit a duration value."""
    segment = "I candidati che hanno conseguito la laurea triennale indicano il voto.\n"
    result = resolve_duration(segment_text=segment)
    assert result.duration_months is None
    assert result.duration_raw is None
    assert result.evidence is None
    assert result.execution_result.winner is None
    assert any(item.reason_code == "guard_blocked" for item in result.execution_result.rejected)
