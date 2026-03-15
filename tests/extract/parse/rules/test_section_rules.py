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


def test_resolve_section_trims_trailing_sul_su_clause() -> None:
    """Section values should stop before trailing 'sul seguente' narrative text."""
    segment = (
        "attività di ricerca tecnologica da usufruire presso la "
        "Sezione di Ferrara dell'I.N.F.N. sul seguente tema di ricerca:"
    )
    result = resolve_section(segment_text=segment)
    assert result.value == "Sezione di Ferrara dell'I.N.F.N."


def test_resolve_section_trims_trailing_finanziato_clause() -> None:
    """Section values should stop before trailing funding narrative text."""
    segment = (
        "attività di ricerca scientifica da usufruire presso la "
        "Sezione di Bologna dell'I.N.F.N. finanziato dal PNRR nell’ambito del progetto"
    )
    result = resolve_section(segment_text=segment)
    assert result.value == "Sezione di Bologna dell'I.N.F.N."


def test_resolve_section_supports_split_tokens_across_lines() -> None:
    """Section rules should resolve values when 'Sezione di' wraps to next line."""
    segment = "attività da usufruire presso la Sezione di\nPisa dell’INFN.\n"
    result = resolve_section(segment_text=segment)
    assert result.value == "Sezione di Pisa dell’INFN."
