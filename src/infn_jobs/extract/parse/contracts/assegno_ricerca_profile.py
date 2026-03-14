"""Overlay profile for Assegno di ricerca contracts."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.base_profile import build_base_profile
from infn_jobs.extract.parse.contracts.profile import ContractProfile


def build_profile() -> ContractProfile:
    """Return profile metadata for Assegno di ricerca extraction rules."""
    return build_base_profile(
        canonical_name="Assegno di ricerca",
        aliases=("Assegno di ricerca",),
        contract_type_patterns=(r"\bASSEGNO\s+DI\s+RICERCA\b",),
        subtype_patterns=(r"\bTipo\s+[AB]\b",),
        subtype_anno_min=2010,
    )
