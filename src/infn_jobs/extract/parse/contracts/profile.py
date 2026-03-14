"""Contract profile model used by parser classification phases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContractProfile:
    """Describe one contract family and its identifying aliases."""

    canonical_name: str
    aliases: tuple[str, ...]
    contract_type_patterns: tuple[str, ...] = ()
    subtype_patterns: tuple[str, ...] = ()
    subtype_anno_min: int | None = None
    subtype_anno_max: int | None = None
