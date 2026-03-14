"""Internal rule builder helpers for contract identity resolution."""

from __future__ import annotations

from infn_jobs.extract.parse.contracts.profile import ContractProfile
from infn_jobs.extract.parse.rules.contract_identity_matching import (
    _FALLBACK_TYPE_RULE_ID,
    _PRIMARY_TYPE_RULE_ID,
    _first_match,
    _select_primary_contract_match,
    _slug,
)
from infn_jobs.extract.parse.rules.models import RuleDefinition


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
                    max_window_lines=2,
                )[0],
                evidence_selector=lambda context, _value, profile=profile: _first_match(
                    context.segment_text,
                    profile.subtype_patterns,
                    max_window_lines=2,
                )[1],
            )
        )
    return tuple(rules)
