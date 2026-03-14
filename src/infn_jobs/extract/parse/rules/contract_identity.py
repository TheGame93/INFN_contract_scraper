"""Rule adapters for contract type/subtype extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infn_jobs.extract.parse.contracts.profile import ContractProfile
from infn_jobs.extract.parse.contracts.registry import list_profiles
from infn_jobs.extract.parse.normalize.subtypes import normalize_subtype
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext, RuleDefinition

_TYPE_PRECEDENCE: dict[str, int] = {
    "Incarico Post-Doc": 10,
    "Contratto di ricerca": 20,
    "Incarico di ricerca": 30,
    "Assegno di ricerca": 40,
    "Borsa di studio": 50,
}
_PRIMARY_TYPE_RULE_ID = "contract_identity.00.first_match.type"
_FALLBACK_TYPE_RULE_ID = "contract_identity.90.predicted_fallback.type"


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


def _slug(value: str) -> str:
    """Return a deterministic slug used in contract-identity rule ids."""
    return (
        value.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(".", "")
    )


def _profile_precedence(profile: ContractProfile) -> int:
    """Return deterministic precedence for same-line contract matches."""
    return _TYPE_PRECEDENCE.get(profile.canonical_name, 80)


def _first_match(
    segment_text: str,
    pattern_texts: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """Return first `(raw_match, evidence_line)` for any pattern, else `(None, None)`."""
    patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in pattern_texts)
    for line in segment_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in patterns:
            match = pattern.search(stripped)
            if match:
                return match.group(0).strip(), stripped
    return None, None


def _select_primary_contract_match(
    segment_text: str,
    profiles: tuple[ContractProfile, ...],
) -> tuple[str, str, str] | None:
    """Return first line contract match as `(canonical, raw, evidence)`."""
    for line in segment_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        line_candidates: list[tuple[int, str, str]] = []
        for profile in profiles:
            raw_match, _ = _first_match(stripped, profile.contract_type_patterns)
            if raw_match is None:
                continue
            line_candidates.append(
                (
                    _profile_precedence(profile),
                    profile.canonical_name,
                    raw_match,
                )
            )
        if line_candidates:
            _, canonical, raw = min(line_candidates, key=lambda item: (item[0], item[1]))
            return canonical, raw, stripped
    return None


def _build_contract_type_rules(
    profiles: tuple[ContractProfile, ...],
) -> tuple[RuleDefinition, ...]:
    """Return deterministic contract-type rules built from profile overlays."""
    return (
        RuleDefinition(
            rule_id=_PRIMARY_TYPE_RULE_ID,
            field_name="contract_type",
            priority_tier="primary",
            transformer=lambda context, profiles=profiles: (
                _select_primary_contract_match(context.segment_text, profiles)[0]
                if _select_primary_contract_match(context.segment_text, profiles) is not None
                else None
            ),
            evidence_selector=lambda context, _value, profiles=profiles: (
                _select_primary_contract_match(context.segment_text, profiles)[2]
                if _select_primary_contract_match(context.segment_text, profiles) is not None
                else None
            ),
        ),
        RuleDefinition(
            rule_id=_FALLBACK_TYPE_RULE_ID,
            field_name="contract_type",
            priority_tier="fallback",
            transformer=lambda context: (
                context.metadata.get("predicted_contract_type")
                if isinstance(context.metadata.get("predicted_contract_type"), str)
                else None
            ),
            evidence_selector=lambda context, _value: next(
                (line.strip() for line in context.segment_text.splitlines() if line.strip()),
                None,
            ),
        ),
    )


def _build_contract_subtype_rules(
    profiles: tuple[ContractProfile, ...],
) -> tuple[RuleDefinition, ...]:
    """Return deterministic contract-subtype rules built from profile overlays."""
    rules: list[RuleDefinition] = []
    for profile in profiles:
        if not profile.subtype_patterns:
            continue
        rules.append(
            RuleDefinition(
                rule_id=f"contract_identity.{_slug(profile.canonical_name)}.subtype",
                field_name="contract_subtype",
                priority_tier="primary",
                contract_filter=(profile.canonical_name,),
                anno_min=profile.subtype_anno_min,
                anno_max=profile.subtype_anno_max,
                transformer=lambda context, profile=profile: _first_match(
                    context.segment_text,
                    profile.subtype_patterns,
                )[0],
                evidence_selector=lambda context, _value, profile=profile: _first_match(
                    context.segment_text,
                    profile.subtype_patterns,
                )[1],
            )
        )
    return tuple(rules)


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

    contract_type = (
        str(type_result.winner.value)
        if type_result.winner is not None
        else None
    )
    contract_type_evidence = (
        type_result.winner.evidence
        if type_result.winner is not None
        else None
    )
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
    contract_subtype_raw = (
        str(subtype_result.winner.value)
        if subtype_result.winner is not None
        else None
    )
    contract_subtype = normalize_subtype(contract_subtype_raw, anno)
    contract_subtype_evidence = (
        subtype_result.winner.evidence
        if subtype_result.winner is not None
        else None
    )

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
