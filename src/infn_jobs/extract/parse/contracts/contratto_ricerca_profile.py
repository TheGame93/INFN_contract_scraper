"""Overlay profile for Contratto di ricerca contracts."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.base_profile import build_base_profile
from infn_jobs.extract.parse.contracts.profile import ContractProfile


def build_profile() -> ContractProfile:
    """Return profile metadata for Contratto di ricerca extraction rules."""
    return build_base_profile(
        canonical_name="Contratto di ricerca",
        aliases=("Contratto di ricerca",),
        contract_type_patterns=(r"\bCONTRATTO\s+DI\s+RICERCA\b",),
        subtype_patterns=(r"\bFascia\s+(?:I{1,3}|[123])\b",),
    )
