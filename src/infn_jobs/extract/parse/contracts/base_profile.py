"""Shared contract-profile defaults used by per-family overlays."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.profile import ContractProfile


def build_base_profile(
    *,
    canonical_name: str,
    aliases: tuple[str, ...],
    contract_type_patterns: tuple[str, ...],
    subtype_patterns: tuple[str, ...] = (),
    subtype_anno_min: int | None = None,
    subtype_anno_max: int | None = None,
) -> ContractProfile:
    """Return one contract profile with common baseline defaults applied."""
    return ContractProfile(
        canonical_name=canonical_name,
        aliases=aliases,
        contract_type_patterns=contract_type_patterns,
        subtype_patterns=subtype_patterns,
        subtype_anno_min=subtype_anno_min,
        subtype_anno_max=subtype_anno_max,
    )
