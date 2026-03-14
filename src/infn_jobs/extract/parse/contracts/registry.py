"""Static registry for known contract profiles."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.assegno_ricerca_profile import (
    build_profile as build_assegno_ricerca_profile,
)
from infn_jobs.extract.parse.contracts.borsa_profile import (
    build_profile as build_borsa_profile,
)
from infn_jobs.extract.parse.contracts.contratto_ricerca_profile import (
    build_profile as build_contratto_ricerca_profile,
)
from infn_jobs.extract.parse.contracts.incarico_postdoc_profile import (
    build_profile as build_incarico_postdoc_profile,
)
from infn_jobs.extract.parse.contracts.incarico_ricerca_profile import (
    build_profile as build_incarico_ricerca_profile,
)
from infn_jobs.extract.parse.contracts.profile import ContractProfile

_PROFILES: tuple[ContractProfile, ...] = (
    build_borsa_profile(),
    build_incarico_ricerca_profile(),
    build_incarico_postdoc_profile(),
    build_contratto_ricerca_profile(),
    build_assegno_ricerca_profile(),
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
