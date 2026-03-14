"""Rule adapters for section/structure extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext, RuleDefinition

_SECTION_PATTERNS: tuple[str, ...] = (
    r"\bSezi?one\s+di\s+\S+(?:\s+\S+){0,3}",
    r"\bSede\s+di\s+\S+(?:\s+\S+){0,3}",
    r"\bStruttura\s+di\s+\S+(?:\s+\S+){0,3}",
)


@dataclass(frozen=True)
class SectionResolution:
    """Resolved section value/evidence plus underlying rule trace."""

    value: str | None
    evidence: str | None
    execution_result: ExecutionResult


def _first_match(
    segment_text: str,
    pattern_texts: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """Return first `(value, evidence_line)` for section patterns, else `(None, None)`."""
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


def _build_section_rules() -> tuple[RuleDefinition, ...]:
    """Return deterministic section extraction rules."""
    return (
        RuleDefinition(
            rule_id="metadata.section.first_match",
            field_name="section_structure_department",
            priority_tier="primary",
            transformer=lambda context: _first_match(
                context.segment_text,
                _SECTION_PATTERNS,
            )[0],
            evidence_selector=lambda context, _value: _first_match(
                context.segment_text,
                _SECTION_PATTERNS,
            )[1],
        ),
    )


def resolve_section(
    *,
    segment_text: str,
    detail_id: str = "",
    anno: int | None = None,
    contract_type: str | None = None,
) -> SectionResolution:
    """Resolve section/structure/department field via deterministic rules."""
    result = execute_rules(
        _build_section_rules(),
        RuleContext(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            contract_type=contract_type,
        ),
    )
    winner = result.winner
    return SectionResolution(
        value=str(winner.value) if winner is not None else None,
        evidence=winner.evidence if winner is not None else None,
        execution_result=result,
    )
