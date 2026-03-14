"""Rule adapters for duration extraction and resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infn_jobs.extract.parse.core.conflict_resolution import merge_execution_results
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext, RuleDefinition

_LABEL_RE = re.compile(
    r"(?:Durata|Periodo|per\s+la\s+durata\s+di|della\s+durata\s+di)\s*:?\s*(.+)",
    re.IGNORECASE,
)
_NUMERIC_RE = re.compile(r"(\d+)(?:\s*\([^)]*\))?\s*mes[ei]", re.IGNORECASE)
_ONE_MONTH_RE = re.compile(r"\bun(?:o)?\s+mes[ei]\b", re.IGNORECASE)
_TRIENNALE_RE = re.compile(r"\btriennale\b", re.IGNORECASE)
_BIENNALE_RE = re.compile(r"\bbiennale\b", re.IGNORECASE)
_ANNUALE_RE = re.compile(r"\b(?:annuale|annuo)\b", re.IGNORECASE)
_FALLBACK_BARE_RE = re.compile(r"^(?:triennale|biennale|annuale|annuo)\W*$", re.IGNORECASE)
_FALLBACK_CONTEXT_RE = re.compile(
    r"\b(?:durata|rinnovabile|usufruire|borsa|assegno|contratto|incarico|attivit[àa])\b",
    re.IGNORECASE,
)
_GUARD_CONTEXT_RE = re.compile(r"\b(?:durata|periodo|rinnovabile|usufruire)\b", re.IGNORECASE)


@dataclass(frozen=True)
class DurationValue:
    """One duration candidate value plus its raw snippet and evidence line."""

    months: int
    raw: str
    evidence: str


@dataclass(frozen=True)
class DurationResolution:
    """Resolved duration fields plus underlying rule execution trace."""

    duration_months: int | None
    duration_raw: str | None
    evidence: str | None
    execution_result: ExecutionResult


def _iter_nonempty_lines(text: str) -> tuple[str, ...]:
    """Return non-empty stripped lines preserving source order."""
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def _extract_labeled_value_text(segment_text: str) -> tuple[str, str] | None:
    """Return `(value_text, evidence_line)` for the first labeled duration line."""
    for line in _iter_nonempty_lines(segment_text):
        match = _LABEL_RE.search(line)
        if match:
            return match.group(1), line
    return None


def _extract_labeled_numeric(segment_text: str) -> DurationValue | None:
    """Return numeric labeled duration candidate when available."""
    labeled = _extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    match = _NUMERIC_RE.search(value_text)
    if match is None:
        return None
    return DurationValue(months=int(match.group(1)), raw=match.group(0).strip(), evidence=evidence)


def _extract_labeled_one_month(segment_text: str) -> DurationValue | None:
    """Return one-month labeled duration candidate when available."""
    labeled = _extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    if _ONE_MONTH_RE.search(value_text):
        return DurationValue(months=1, raw="un mese", evidence=evidence)
    return None


def _extract_labeled_word(
    segment_text: str,
    *,
    pattern: re.Pattern[str],
    months: int,
    raw: str,
) -> DurationValue | None:
    """Return labeled word-based duration candidate when available."""
    labeled = _extract_labeled_value_text(segment_text)
    if labeled is None:
        return None
    value_text, evidence = labeled
    if pattern.search(value_text):
        return DurationValue(months=months, raw=raw, evidence=evidence)
    return None


def _extract_bare_word(
    segment_text: str,
    *,
    pattern: re.Pattern[str],
    months: int,
    raw: str,
) -> DurationValue | None:
    """Return bare-word duration candidate when line context allows it."""
    for line in _iter_nonempty_lines(segment_text):
        if not pattern.search(line):
            continue
        if _FALLBACK_BARE_RE.match(line) or _FALLBACK_CONTEXT_RE.search(line):
            return DurationValue(months=months, raw=raw, evidence=line)
    return None


def _extract_numeric_guarded(segment_text: str) -> DurationValue | None:
    """Return guarded numeric duration candidate as final fallback."""
    for line in _iter_nonempty_lines(segment_text):
        if not _GUARD_CONTEXT_RE.search(line):
            continue
        match = _NUMERIC_RE.search(line)
        if match:
            return DurationValue(
                months=int(match.group(1)),
                raw=match.group(0).strip(),
                evidence=line,
            )
    return None


def _has_duration_context(context: RuleContext) -> bool:
    """Return True when segment includes duration-like context words."""
    return _FALLBACK_CONTEXT_RE.search(context.segment_text) is not None


def _duration_primary_rules() -> tuple[RuleDefinition, ...]:
    """Return primary duration rules with labeled evidence precedence."""
    return (
        RuleDefinition(
            rule_id="duration.primary.10.labeled_numeric",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _extract_labeled_numeric(context.segment_text),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.20.labeled_one_month",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _extract_labeled_one_month(context.segment_text),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.30.labeled_triennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _extract_labeled_word(
                context.segment_text,
                pattern=_TRIENNALE_RE,
                months=36,
                raw="triennale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.40.labeled_biennale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _extract_labeled_word(
                context.segment_text,
                pattern=_BIENNALE_RE,
                months=24,
                raw="biennale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.primary.50.labeled_annuale",
            field_name="duration",
            priority_tier="primary",
            transformer=lambda context: _extract_labeled_word(
                context.segment_text,
                pattern=_ANNUALE_RE,
                months=12,
                raw="annuale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_fallback_rules() -> tuple[RuleDefinition, ...]:
    """Return fallback duration rules for bare word expressions."""
    return (
        RuleDefinition(
            rule_id="duration.fallback.10.bare_triennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _extract_bare_word(
                context.segment_text,
                pattern=_TRIENNALE_RE,
                months=36,
                raw="triennale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.20.bare_biennale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _extract_bare_word(
                context.segment_text,
                pattern=_BIENNALE_RE,
                months=24,
                raw="biennale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
        RuleDefinition(
            rule_id="duration.fallback.30.bare_annuale",
            field_name="duration",
            priority_tier="fallback",
            guards=(_has_duration_context,),
            transformer=lambda context: _extract_bare_word(
                context.segment_text,
                pattern=_ANNUALE_RE,
                months=12,
                raw="annuale",
            ),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def _duration_guard_rules() -> tuple[RuleDefinition, ...]:
    """Return guard-tier duration rules for constrained numeric fallback."""
    return (
        RuleDefinition(
            rule_id="duration.guard.10.numeric_context",
            field_name="duration",
            priority_tier="guard",
            guards=(_has_duration_context,),
            transformer=lambda context: _extract_numeric_guarded(context.segment_text),
            evidence_selector=lambda _context, value: value.evidence,
        ),
    )


def resolve_duration(
    *,
    segment_text: str,
    detail_id: str = "",
    anno: int | None = None,
    contract_type: str | None = None,
) -> DurationResolution:
    """Resolve duration fields via primary/fallback/guard rule groups."""
    context = RuleContext(
        segment_text=segment_text,
        detail_id=detail_id,
        anno=anno,
        contract_type=contract_type,
    )
    merged = merge_execution_results(
        (
            execute_rules(_duration_primary_rules(), context),
            execute_rules(_duration_fallback_rules(), context),
            execute_rules(_duration_guard_rules(), context),
        )
    )

    winner = merged.winner
    if winner is None or not isinstance(winner.value, DurationValue):
        return DurationResolution(
            duration_months=None,
            duration_raw=None,
            evidence=None,
            execution_result=merged,
        )
    return DurationResolution(
        duration_months=winner.value.months,
        duration_raw=winner.value.raw,
        evidence=winner.value.evidence,
        execution_result=merged,
    )
