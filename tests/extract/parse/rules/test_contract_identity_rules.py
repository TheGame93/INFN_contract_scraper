"""Tests for contract identity rule adapters."""

from infn_jobs.extract.parse.rules.contract_identity import resolve_contract_identity


def test_resolve_contract_identity_extracts_assegno_type_and_semantic_subtype() -> None:
    """Contract identity rules should resolve Assegno type and canonical semantic subtype."""
    result = resolve_contract_identity(
        segment_text="ASSEGNO DI RICERCA - Tipo B\nSezione di Roma",
        anno=2015,
    )
    assert result.contract_type == "Assegno di ricerca"
    assert result.contract_type_raw == "ASSEGNO DI RICERCA"
    assert result.contract_subtype == "Senior"
    assert result.contract_subtype_raw == "Tipo B"
    assert result.contract_type_result.winner is not None
    assert result.contract_subtype_result.winner is not None


def test_resolve_contract_identity_uses_predicted_fallback() -> None:
    """Fallback rule should use predicted contract type when no primary match exists."""
    result = resolve_contract_identity(
        segment_text="Titolo della selezione\nNessun pattern esplicito",
        anno=2026,
        predicted_contract_type="Incarico di ricerca",
    )
    assert result.contract_type == "Incarico di ricerca"
    assert result.contract_type_raw == "Incarico di ricerca"
    assert result.contract_type_result.winner is not None
    assert (
        result.contract_type_result.winner.rule_id
        == "contract_identity.90.predicted_fallback.type"
    )


def test_resolve_contract_identity_gates_assegno_subtype_pre_2010() -> None:
    """Assegno subtype rules should not emit Tipo A/B before 2010."""
    result = resolve_contract_identity(
        segment_text="ASSEGNO DI RICERCA - Tipo A\nSezione di Frascati",
        anno=2007,
    )
    assert result.contract_type == "Assegno di ricerca"
    assert result.contract_subtype is None
    assert result.contract_subtype_raw is None
    assert any(
        item.reason_code == "era_mismatch"
        for item in result.contract_subtype_result.rejected
    )


def test_resolve_contract_identity_normalizes_fascia_1_subtype() -> None:
    """Incarico profile should resolve Fascia 1 subtype with canonical normalization."""
    result = resolve_contract_identity(
        segment_text="INCARICO DI RICERCA\nrinnovabile, di Fascia 1, da fruire presso la Sezione.",
        anno=2026,
    )
    assert result.contract_type == "Incarico di ricerca"
    assert result.contract_subtype == "Fascia 1"
    assert result.contract_subtype_raw == "Fascia 1"
    assert result.contract_subtype_evidence is not None


def test_resolve_contract_identity_supports_multiline_subtype_tokens() -> None:
    """Subtype rules should resolve Fascia values when roman token is on next line."""
    result = resolve_contract_identity(
        segment_text="INCARICO DI RICERCA\nFascia\nIII\nSezione di Roma",
        anno=2026,
    )
    assert result.contract_type == "Incarico di ricerca"
    assert result.contract_subtype == "Fascia 3"
    assert result.contract_subtype_raw == "Fascia III"
    assert result.contract_subtype_evidence is not None
    assert "Fascia III" in result.contract_subtype_evidence


def test_resolve_contract_identity_supports_split_contract_type_tokens() -> None:
    """Type rules should resolve when contract-type tokens are split across lines."""
    result = resolve_contract_identity(
        segment_text="CONTRATTO DI\nRICERCA\nFascia\n1\nSezione di Pisa",
        anno=2026,
    )
    assert result.contract_type == "Contratto di ricerca"
    assert result.contract_type_raw == "CONTRATTO DI RICERCA"
    assert result.contract_subtype == "Fascia 1"
    assert result.contract_subtype_raw == "Fascia 1"
