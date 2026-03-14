"""Rule adapters for income and cost field extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from infn_jobs.extract.parse.normalize.currency import normalize_eur
from infn_jobs.extract.parse.rules.executor import execute_rules
from infn_jobs.extract.parse.rules.models import ExecutionResult, RuleContext, RuleDefinition

_CURRENCY_ANCHORED_RE = re.compile(r"(?:€|euro)\s*([\d][\d.,\s]*)", re.IGNORECASE)
_FORMATTED_AMOUNT_RE = re.compile(r"\d[\d.]*,\d{1,2}|\d+\.\d{2}")
_BARE_AMOUNT_RE = re.compile(r"[\d][\d.,\s]*")

_INSTITUTE_RE = re.compile(
    r"(?:Costo\s+a\s+carico\s+dell['\u2019]?Ente|Costo\s+istituzionale)",
    re.IGNORECASE,
)
_GROSS_RE = re.compile(
    r"(?:Compenso|Importo|Reddito)\s+lordo|Retribuzione\s+lorda",
    re.IGNORECASE,
)
_NET_RE = re.compile(r"(?:Compenso|Importo|Reddito)\s+netto", re.IGNORECASE)

_TOTAL_RE = re.compile(r"\btotale\b", re.IGNORECASE)
_YEARLY_RE = re.compile(r"\b(?:annuo|annuale)\b", re.IGNORECASE)
_MONTHLY_RE = re.compile(r"\bmensile\b", re.IGNORECASE)


@dataclass(frozen=True)
class IncomeAmount:
    """One parsed EUR amount candidate plus its evidence line."""

    value: float
    evidence: str


@dataclass(frozen=True)
class IncomeResolution:
    """Resolved income fields and per-field execution traces."""

    values: dict[str, float | str | None]
    execution_results: dict[str, ExecutionResult]


def _iter_lines(segment_text: str) -> tuple[str, ...]:
    """Return non-empty stripped segment lines preserving source order."""
    return tuple(line.strip() for line in segment_text.splitlines() if line.strip())


def _extract_amount(line: str, start_pos: int = 0) -> float | None:
    """Extract amount from one line using stable precedence patterns."""
    for pattern, group in (
        (_CURRENCY_ANCHORED_RE, 1),
        (_FORMATTED_AMOUNT_RE, 0),
        (_BARE_AMOUNT_RE, 0),
    ):
        match = pattern.search(line, pos=start_pos)
        if match is None:
            continue
        value = normalize_eur(match.group(group))
        if value is not None:
            return value
    return None


def _line_has_no_qualifier(line: str) -> bool:
    """Return True when line has no total/yearly/monthly qualifier token."""
    return not (_TOTAL_RE.search(line) or _YEARLY_RE.search(line) or _MONTHLY_RE.search(line))


def _find_amount(
    *,
    segment_text: str,
    label_re: re.Pattern[str],
    require_total: bool = False,
    require_yearly: bool = False,
    require_monthly: bool = False,
    require_no_qualifier: bool = False,
) -> IncomeAmount | None:
    """Return last matching amount/evidence candidate for the given constraints."""
    candidate: IncomeAmount | None = None
    for line in _iter_lines(segment_text):
        label_match = label_re.search(line)
        if label_match is None:
            continue
        if require_total and _TOTAL_RE.search(line) is None:
            continue
        if require_yearly and _YEARLY_RE.search(line) is None:
            continue
        if require_monthly and _MONTHLY_RE.search(line) is None:
            continue
        if require_no_qualifier and not _line_has_no_qualifier(line):
            continue
        amount = _extract_amount(line, start_pos=label_match.end())
        if amount is None:
            continue
        candidate = IncomeAmount(value=amount, evidence=line)
    return candidate


def _rules_for_field(field_name: str) -> tuple[RuleDefinition, ...]:
    """Return deterministic rule set for one income field."""
    if field_name == "institute_cost_total_eur":
        return (
            RuleDefinition(
                rule_id="income.institute.total.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_INSTITUTE_RE,
                    require_total=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
            RuleDefinition(
                rule_id="income.institute.total.fallback_unqualified",
                field_name=field_name,
                priority_tier="fallback",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_INSTITUTE_RE,
                    require_no_qualifier=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "institute_cost_yearly_eur":
        return (
            RuleDefinition(
                rule_id="income.institute.yearly.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_INSTITUTE_RE,
                    require_yearly=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "gross_income_total_eur":
        return (
            RuleDefinition(
                rule_id="income.gross.total.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_GROSS_RE,
                    require_total=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "gross_income_yearly_eur":
        return (
            RuleDefinition(
                rule_id="income.gross.yearly.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_GROSS_RE,
                    require_yearly=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
            RuleDefinition(
                rule_id="income.gross.yearly.fallback_unqualified",
                field_name=field_name,
                priority_tier="fallback",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_GROSS_RE,
                    require_no_qualifier=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "net_income_total_eur":
        return (
            RuleDefinition(
                rule_id="income.net.total.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_NET_RE,
                    require_total=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "net_income_yearly_eur":
        return (
            RuleDefinition(
                rule_id="income.net.yearly.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_NET_RE,
                    require_yearly=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
            RuleDefinition(
                rule_id="income.net.yearly.fallback_unqualified",
                field_name=field_name,
                priority_tier="fallback",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_NET_RE,
                    require_no_qualifier=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    if field_name == "net_income_monthly_eur":
        return (
            RuleDefinition(
                rule_id="income.net.monthly.primary",
                field_name=field_name,
                priority_tier="primary",
                transformer=lambda context: _find_amount(
                    segment_text=context.segment_text,
                    label_re=_NET_RE,
                    require_monthly=True,
                ),
                evidence_selector=lambda _context, value: value.evidence,
            ),
        )

    raise ValueError(f"Unsupported income field: {field_name}")


def _resolve_field(
    field_name: str,
    context: RuleContext,
) -> tuple[float | None, str | None, ExecutionResult]:
    """Resolve one income field via deterministic rules."""
    result = execute_rules(_rules_for_field(field_name), context)
    winner = result.winner
    if winner is None or not isinstance(winner.value, IncomeAmount):
        return None, None, result
    return winner.value.value, winner.value.evidence, result


def _pick_group_evidence(
    values: dict[str, float | str | None],
    *,
    monthly_key: str | None = None,
    total_key: str | None = None,
    yearly_key: str | None = None,
) -> str | None:
    """Return deterministic group evidence by qualifier preference."""
    evidence_lookup = {
        "monthly": f"{monthly_key}_evidence" if monthly_key else None,
        "total": f"{total_key}_evidence" if total_key else None,
        "yearly": f"{yearly_key}_evidence" if yearly_key else None,
    }
    for order_key in ("monthly", "total", "yearly"):
        key = evidence_lookup[order_key]
        if key is None:
            continue
        evidence = values.get(key)
        if isinstance(evidence, str):
            return evidence
    return None


def resolve_income(
    *,
    segment_text: str,
    detail_id: str = "",
    anno: int | None = None,
    contract_type: str | None = None,
) -> IncomeResolution:
    """Resolve all income fields through rule-driven per-field adapters."""
    context = RuleContext(
        segment_text=segment_text,
        detail_id=detail_id,
        anno=anno,
        contract_type=contract_type,
    )
    values: dict[str, float | str | None] = {
        "institute_cost_total_eur": None,
        "institute_cost_yearly_eur": None,
        "gross_income_total_eur": None,
        "gross_income_yearly_eur": None,
        "net_income_total_eur": None,
        "net_income_yearly_eur": None,
        "net_income_monthly_eur": None,
        "institute_cost_evidence": None,
        "gross_income_evidence": None,
        "net_income_evidence": None,
    }
    execution_results: dict[str, ExecutionResult] = {}

    for field_name in (
        "institute_cost_total_eur",
        "institute_cost_yearly_eur",
        "gross_income_total_eur",
        "gross_income_yearly_eur",
        "net_income_total_eur",
        "net_income_yearly_eur",
        "net_income_monthly_eur",
    ):
        amount, evidence, result = _resolve_field(field_name, context)
        values[field_name] = amount
        values[f"{field_name}_evidence"] = evidence
        execution_results[field_name] = result

    values["institute_cost_evidence"] = _pick_group_evidence(
        values,
        total_key="institute_cost_total_eur",
        yearly_key="institute_cost_yearly_eur",
    )
    values["gross_income_evidence"] = _pick_group_evidence(
        values,
        total_key="gross_income_total_eur",
        yearly_key="gross_income_yearly_eur",
    )
    values["net_income_evidence"] = _pick_group_evidence(
        values,
        monthly_key="net_income_monthly_eur",
        total_key="net_income_total_eur",
        yearly_key="net_income_yearly_eur",
    )

    return IncomeResolution(values=values, execution_results=execution_results)
