"""Overlay profile for Borsa di studio contracts."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.base_profile import build_base_profile
from infn_jobs.extract.parse.contracts.profile import ContractProfile


def build_profile() -> ContractProfile:
    """Return profile metadata for Borsa di studio extraction rules."""
    return build_base_profile(
        canonical_name="Borsa di studio",
        aliases=("Borsa di studio", "Borsa"),
        contract_type_patterns=(r"\bBORSA(?:\s+DI\s+STUDIO)?\b",),
    )
