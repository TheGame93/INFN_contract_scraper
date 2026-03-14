"""Rule adapters for contract type/subtype extraction."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.contracts.registry import list_profiles
from infn_jobs.extract.parse.normalize.subtypes import normalize_subtype
from infn_jobs.extract.parse.rules.contract_identity_matching import (
    _FALLBACK_TYPE_RULE_ID,
    _select_primary_contract_match,
)
from infn_jobs.extract.parse.rules.contract_identity_rule_builders import (
    _build_contract_subtype_rules,
    _build_contract_type_rules,
)
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext


@dataclass(frozen=True)
class ContractIdentityResolution:
    """Resolved contract identity/subtype values plus underlying rule traces."""

    contract_type: str | None
    contract_type_raw: str | None
    contract_type_evidence: str | None
    contract_subtype: str | None
    contract_subtype_raw: str | None
    contract_subtype_evidence: str | None
    contract_type_result: ExecutionResult
    contract_subtype_result: ExecutionResult


def resolve_contract_identity(
    *,
    segment_text: str,
    anno: int | None,
    predicted_contract_type: str | None = None,
    detail_id: str = "",
) -> ContractIdentityResolution:
    """Resolve contract type/subtype fields via deterministic profile-aware rules."""
    profiles = list_profiles()
    type_result = execute_rules(
        _build_contract_type_rules(profiles),
        RuleContext(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            metadata={"predicted_contract_type": predicted_contract_type},
        ),
    )

    contract_type = str(type_result.winner.value) if type_result.winner is not None else None
    contract_type_evidence = type_result.winner.evidence if type_result.winner is not None else None
    contract_type_raw: str | None = None
    if type_result.winner is not None:
        if type_result.winner.rule_id == _FALLBACK_TYPE_RULE_ID:
            contract_type_raw = contract_type
        else:
            primary_match = _select_primary_contract_match(segment_text, profiles)
            contract_type_raw = primary_match[1] if primary_match is not None else None

    subtype_result = execute_rules(
        _build_contract_subtype_rules(profiles),
        RuleContext(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            contract_type=contract_type,
        ),
    )
    contract_subtype_raw = str(subtype_result.winner.value) if subtype_result.winner else None
    contract_subtype = normalize_subtype(contract_subtype_raw, anno)
    contract_subtype_evidence = subtype_result.winner.evidence if subtype_result.winner else None

    return ContractIdentityResolution(
        contract_type=contract_type,
        contract_type_raw=contract_type_raw,
        contract_type_evidence=contract_type_evidence,
        contract_subtype=contract_subtype,
        contract_subtype_raw=contract_subtype_raw,
        contract_subtype_evidence=contract_subtype_evidence,
        contract_type_result=type_result,
        contract_subtype_result=subtype_result,
    )
