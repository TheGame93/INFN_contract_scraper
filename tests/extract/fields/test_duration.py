"""Tests for the duration field extractor."""

from pathlib import Path

from infn_jobs.extract.parse.fields.duration import extract_duration

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_extract_duration_mesi_label():
    months, raw, ev = extract_duration(_read("single_contract.txt"))
    assert months == 12
    assert "12" in raw


def test_extract_duration_biennale():
    months, raw, _ = extract_duration("CONTRATTO DI RICERCA\nbiennale\n")
    assert months == 24
    assert raw == "biennale"


def test_extract_duration_triennale():
    months, raw, _ = extract_duration("ASSEGNO DI RICERCA\nDurata: triennale\n")
    assert months == 36


def test_extract_duration_era_variant_della_durata_di():
    months, raw, ev = extract_duration("della durata di 24 mesi\n")
    assert months == 24
    assert "24" in raw
    assert ev is not None


def test_extract_duration_era_variant_periodo():
    months, raw, ev = extract_duration("Periodo: 12 mesi\n")
    assert months == 12
    assert "12" in raw


def test_extract_duration_parenthetical_number():
    months, raw, _ = extract_duration("Durata: 24 (venti quattro) mesi\n")
    assert months == 24
    assert "24" in raw


def test_extract_duration_missing_returns_triple_none():
    months, raw, ev = extract_duration("BORSA DI STUDIO\nSezione di Bari\n")
    assert months is None
    assert raw is None
    assert ev is None


def test_extract_duration_evidence_captured():
    _, _, ev = extract_duration(_read("single_contract.txt"))
    assert ev is not None
    assert "Durata" in ev or "durata" in ev.lower()


def test_extract_duration_prefers_labeled_duration_over_unrelated_triennale():
    segment = (
        "I candidati che hanno conseguito la laurea triennale devono indicare il voto.\n"
        "Durata: 12 mesi\n"
    )
    months, raw, ev = extract_duration(segment)
    assert months == 12
    assert raw is not None and "12" in raw
    assert ev == "Durata: 12 mesi"


def test_extract_duration_does_not_use_laurea_triennale_line_as_duration():
    segment = "I candidati che hanno conseguito la laurea triennale devono indicare il voto.\n"
    months, raw, ev = extract_duration(segment)
    assert months is None
    assert raw is None
    assert ev is None


def test_extract_duration_label_with_un_mese():
    segment = "La durata di ciascuna borsa è di un mese.\n"
    months, raw, ev = extract_duration(segment)
    assert months == 1
    assert raw == "un mese"
    assert ev is not None
