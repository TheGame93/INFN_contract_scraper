"""Deterministic pipeline-level row-cardinality reconciliation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.domain.position import PositionRow

_PARSE_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
_INCOME_FIELDS = (
    "institute_cost_total_eur",
    "institute_cost_yearly_eur",
    "gross_income_total_eur",
    "gross_income_yearly_eur",
    "net_income_total_eur",
    "net_income_yearly_eur",
    "net_income_monthly_eur",
)
_MISSING_INDEX_SENTINEL = 1_000_000_000


@dataclass(frozen=True)
class ReconciliationDecision:
    """Deterministic row-reconciliation decision metadata for one detail_id."""

    detail_id: str
    numero_posti_html: int | None
    raw_rows: int
    kept_rows: int
    applied: bool
    reason_code: str


def _parse_confidence_rank(value: str | None) -> int:
    """Return sortable confidence rank for one parse_confidence value."""
    if value is None:
        return 0
    return _PARSE_CONFIDENCE_RANK.get(value.lower(), 0)


def _position_index_rank(row: PositionRow) -> int:
    """Return sortable position-row index where lower indices rank higher."""
    index = row.position_row_index
    if isinstance(index, bool):
        return _MISSING_INDEX_SENTINEL
    if isinstance(index, int):
        return index
    return _MISSING_INDEX_SENTINEL


def _income_signal_count(row: PositionRow) -> int:
    """Return count of non-null income signals for one row."""
    return sum(1 for field in _INCOME_FIELDS if getattr(row, field) is not None)


def _row_strength_key(row: PositionRow) -> tuple[int, int, int, int, int, int, int]:
    """Return deterministic strength key used to pick one best row."""
    return (
        int(bool(row.contract_type)),
        int(bool(row.contract_subtype)),
        int(row.duration_months is not None),
        _income_signal_count(row),
        int(bool(row.section_structure_department) or bool(row.section_evidence)),
        _parse_confidence_rank(row.parse_confidence),
        -_position_index_rank(row),
    )


def _reason_for_non_authoritative_numero_posti(numero_posti_html: int | None) -> str:
    """Return deterministic no-op reason code for non-authoritative posti values."""
    if numero_posti_html is None:
        return "not_applicable_numero_posti_missing"
    if isinstance(numero_posti_html, bool) or not isinstance(numero_posti_html, int):
        return "not_applicable_numero_posti_invalid"
    if numero_posti_html != 1:
        return "not_applicable_numero_posti_not_one"
    return "applied_numero_posti_singleton_guard"


def reconcile_rows(
    *,
    rows: list[PositionRow],
    detail_id: str,
    numero_posti_html: int | None,
) -> tuple[list[PositionRow], ReconciliationDecision]:
    """Return reconciled rows plus deterministic decision metadata."""
    raw_rows = len(rows)
    if raw_rows <= 1:
        return (
            list(rows),
            ReconciliationDecision(
                detail_id=detail_id,
                numero_posti_html=numero_posti_html,
                raw_rows=raw_rows,
                kept_rows=raw_rows,
                applied=False,
                reason_code="not_applicable_single_or_empty",
            ),
        )

    reason_code = _reason_for_non_authoritative_numero_posti(numero_posti_html)
    if reason_code != "applied_numero_posti_singleton_guard":
        return (
            list(rows),
            ReconciliationDecision(
                detail_id=detail_id,
                numero_posti_html=numero_posti_html,
                raw_rows=raw_rows,
                kept_rows=raw_rows,
                applied=False,
                reason_code=reason_code,
            ),
        )

    winner = max(rows, key=_row_strength_key)
    return (
        [winner],
        ReconciliationDecision(
            detail_id=detail_id,
            numero_posti_html=numero_posti_html,
            raw_rows=raw_rows,
            kept_rows=1,
            applied=True,
            reason_code=reason_code,
        ),
    )
