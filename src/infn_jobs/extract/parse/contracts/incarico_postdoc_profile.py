"""Overlay profile for Incarico Post-Doc contracts."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.base_profile import build_base_profile
from infn_jobs.extract.parse.contracts.profile import ContractProfile


def build_profile() -> ContractProfile:
    """Return profile metadata for Incarico Post-Doc extraction rules."""
    return build_base_profile(
        canonical_name="Incarico Post-Doc",
        aliases=("Incarico Post-Doc", "Incarico postdoc"),
        contract_type_patterns=(r"\bINCARICO\s+POST[-\s]?DOC\b",),
        subtype_patterns=(r"\bFascia\s+(?:I{1,3}|[123])\b",),
    )
