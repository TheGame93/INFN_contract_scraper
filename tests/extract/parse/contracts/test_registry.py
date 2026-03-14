"""Tests for contract profile registry helpers."""

from infn_jobs.extract.parse.contracts.registry import get_profile, list_profiles


def test_list_profiles_contains_five_expected_contract_families() -> None:
    """Registry should expose all current contract profiles in deterministic order."""
    names = [profile.canonical_name for profile in list_profiles()]
    assert names == [
        "Borsa di studio",
        "Incarico di ricerca",
        "Incarico Post-Doc",
        "Contratto di ricerca",
        "Assegno di ricerca",
    ]


def test_get_profile_returns_profile_or_none() -> None:
    """get_profile should resolve known names and return None for unknown ones."""
    profile = get_profile("Incarico Post-Doc")
    assert profile is not None
    assert profile.canonical_name == "Incarico Post-Doc"
    assert "Incarico postdoc" in profile.aliases
    assert get_profile("unknown-profile") is None

