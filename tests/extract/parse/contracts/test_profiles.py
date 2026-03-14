"""Tests for concrete contract profile overlays."""

from infn_jobs.extract.parse.contracts.registry import get_profile


def test_profiles_expose_type_patterns_for_each_contract_family() -> None:
    """Each known profile should define at least one contract-type pattern."""
    expected = (
        "Borsa di studio",
        "Incarico di ricerca",
        "Incarico Post-Doc",
        "Contratto di ricerca",
        "Assegno di ricerca",
    )
    for canonical_name in expected:
        profile = get_profile(canonical_name)
        assert profile is not None
        assert profile.contract_type_patterns


def test_assegno_profile_has_tipo_ab_subtype_and_post_2010_gate() -> None:
    """Assegno overlay should gate Tipo A/B subtype extraction by era."""
    profile = get_profile("Assegno di ricerca")
    assert profile is not None
    assert profile.subtype_patterns == (r"\bTipo\s+[AB]\b",)
    assert profile.subtype_anno_min == 2010
    assert profile.subtype_anno_max is None


def test_non_assegno_profiles_keep_no_subtype_era_gate() -> None:
    """Other overlays should not add subtype era restrictions."""
    for canonical_name in (
        "Borsa di studio",
        "Incarico di ricerca",
        "Incarico Post-Doc",
        "Contratto di ricerca",
    ):
        profile = get_profile(canonical_name)
        assert profile is not None
        assert profile.subtype_anno_min is None
        assert profile.subtype_anno_max is None
