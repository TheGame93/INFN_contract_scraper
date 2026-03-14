"""Tests for section extraction rule adapters."""

from infn_jobs.extract.parse.rules.section import resolve_section


def test_resolve_section_extracts_value_and_evidence() -> None:
    """Section rules should return matched value and the original evidence line."""
    result = resolve_section(segment_text="Sezione di Roma 1\nAltra riga")
    assert result.value == "Sezione di Roma 1"
    assert result.evidence == "Sezione di Roma 1"
    assert result.execution_result.winner is not None


def test_resolve_section_prefers_first_match_in_segment_order() -> None:
    """Section rules should deterministically pick the first matching line."""
    result = resolve_section(
        segment_text="Sede di Napoli\nSezione di Roma 1\nStruttura di Frascati",
    )
    assert result.value == "Sede di Napoli"
    assert result.evidence == "Sede di Napoli"


def test_resolve_section_returns_none_when_missing() -> None:
    """Section rules should return nulls when no section-like pattern is found."""
    result = resolve_section(segment_text="Nessuna corrispondenza")
    assert result.value is None
    assert result.evidence is None
    assert result.execution_result.winner is None
