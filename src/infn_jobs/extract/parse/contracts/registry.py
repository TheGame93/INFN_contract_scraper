"""Static registry for known contract profiles."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.profile import ContractProfile

_PROFILES: tuple[ContractProfile, ...] = (
    ContractProfile(
        canonical_name="Borsa di studio",
        aliases=("Borsa di studio", "Borsa"),
    ),
    ContractProfile(
        canonical_name="Incarico di ricerca",
        aliases=("Incarico di ricerca",),
    ),
    ContractProfile(
        canonical_name="Incarico Post-Doc",
        aliases=("Incarico Post-Doc", "Incarico postdoc"),
    ),
    ContractProfile(
        canonical_name="Contratto di ricerca",
        aliases=("Contratto di ricerca",),
    ),
    ContractProfile(
        canonical_name="Assegno di ricerca",
        aliases=("Assegno di ricerca",),
    ),
)


def list_profiles() -> tuple[ContractProfile, ...]:
    """Return all known contract profiles in deterministic order."""
    return _PROFILES


def get_profile(canonical_name: str) -> ContractProfile | None:
    """Return profile for canonical_name, or None when unknown."""
    for profile in _PROFILES:
        if profile.canonical_name == canonical_name:
            return profile
    return None


def profile_alias_map() -> dict[str, str]:
    """Return alias -> canonical contract name mapping."""
    aliases: dict[str, str] = {}
    for profile in _PROFILES:
        for alias in profile.aliases:
            aliases[alias.lower()] = profile.canonical_name
    return aliases
