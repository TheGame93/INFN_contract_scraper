"""Tests for the contract_type field extractor."""

from pathlib import Path

from infn_jobs.extract.parse.fields.contract_type import extract_contract_type

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_extract_contract_type_contratto_ricerca():
    result = extract_contract_type(_read("single_contract.txt"), 2022)
    assert result["contract_type"] == "Contratto di ricerca"
    assert result["contract_type_raw"] == "CONTRATTO DI RICERCA"


def test_extract_contract_type_borsa():
    result = extract_contract_type(_read("missing_fields.txt"), 2005)
    assert result["contract_type"] == "Borsa di studio"


def test_extract_contract_type_assegno_tipo_a_post2010():
    text = _read("assegno_tipo_ab.txt")
    # First segment contains "Tipo A"
    from infn_jobs.extract.parse.segmenter import segment
    segs = segment(text)
    result = extract_contract_type(segs[0], 2015)
    assert result["contract_type"] == "Assegno di ricerca"
    assert result["contract_subtype"] == "Tipo A"


def test_extract_contract_type_assegno_tipo_b_post2010():
    text = _read("assegno_tipo_ab.txt")
    from infn_jobs.extract.parse.segmenter import segment
    segs = segment(text)
    result = extract_contract_type(segs[1], 2015)
    assert result["contract_subtype"] == "Tipo B"


def test_extract_contract_type_assegno_pre2010_subtype_is_none():
    result = extract_contract_type(_read("assegno_old.txt"), 2007)
    assert result["contract_subtype"] is None


def test_extract_contract_type_fascia_ii_normalized_to_fascia_2():
    seg = "INCARICO DI RICERCA\nFascia II\nDurata: 12 mesi"
    result = extract_contract_type(seg, 2015)
    assert result["contract_subtype"] == "Fascia 2"
    assert result["contract_subtype_raw"] == "Fascia II"


def test_extract_contract_type_missing_returns_all_none():
    result = extract_contract_type("Nessun tipo di contratto qui.", None)
    assert result["contract_type"] is None
    assert result["contract_type_raw"] is None
    assert result["contract_subtype"] is None


def test_extract_contract_type_evidence_captured():
    result = extract_contract_type(_read("single_contract.txt"), 2022)
    assert result["contract_type_evidence"] is not None
    assert "CONTRATTO" in result["contract_type_evidence"].upper()


def test_extract_contract_type_returns_stable_key_set():
    result = extract_contract_type("ASSEGNO DI RICERCA - Tipo A", 2022)
    assert set(result.keys()) == {
        "contract_type",
        "contract_type_raw",
        "contract_type_evidence",
        "contract_subtype",
        "contract_subtype_raw",
        "contract_subtype_evidence",
    }
