"""Unit tests for deterministic pipeline row-cardinality reconciliation."""

from infn_jobs.domain.position import PositionRow
from infn_jobs.pipeline.row_reconciliation import reconcile_rows


def test_reconcile_rows_applies_singleton_guard_and_keeps_strongest_row() -> None:
    """numero_posti_html=1 with multi-row output must keep one strongest row."""
    weak = PositionRow(detail_id="x", position_row_index=0, parse_confidence="low")
    strong = PositionRow(
        detail_id="x",
        position_row_index=1,
        contract_type="Borsa di studio",
        contract_subtype="Fascia 1",
        duration_months=12,
        gross_income_yearly_eur=1234.0,
        section_structure_department="Sezione di Pisa",
        parse_confidence="high",
    )

    rows, decision = reconcile_rows(rows=[weak, strong], detail_id="x", numero_posti_html=1)

    assert [row.position_row_index for row in rows] == [1]
    assert decision.applied is True
    assert decision.reason_code == "applied_numero_posti_singleton_guard"
    assert decision.raw_rows == 2
    assert decision.kept_rows == 1


def test_reconcile_rows_is_noop_when_numero_posti_html_missing() -> None:
    """Missing numero_posti_html must keep all parsed rows unchanged."""
    rows_input = [
        PositionRow(detail_id="x", position_row_index=0, contract_type="Borsa di studio"),
        PositionRow(detail_id="x", position_row_index=1, contract_type="Incarico di ricerca"),
    ]

    rows, decision = reconcile_rows(rows=rows_input, detail_id="x", numero_posti_html=None)

    assert [row.position_row_index for row in rows] == [0, 1]
    assert decision.applied is False
    assert decision.reason_code == "not_applicable_numero_posti_missing"
    assert decision.raw_rows == 2
    assert decision.kept_rows == 2


def test_reconcile_rows_is_noop_when_numero_posti_html_is_not_one() -> None:
    """numero_posti_html values other than 1 must keep all parsed rows."""
    rows_input = [
        PositionRow(detail_id="x", position_row_index=0, contract_type="Borsa di studio"),
        PositionRow(detail_id="x", position_row_index=1, contract_type="Incarico di ricerca"),
    ]

    rows, decision = reconcile_rows(rows=rows_input, detail_id="x", numero_posti_html=2)

    assert [row.position_row_index for row in rows] == [0, 1]
    assert decision.applied is False
    assert decision.reason_code == "not_applicable_numero_posti_not_one"


def test_reconcile_rows_tie_break_prefers_lowest_original_index() -> None:
    """Equal-strength rows must break ties by lowest original position_row_index."""
    row_a = PositionRow(
        detail_id="x",
        position_row_index=5,
        contract_type="Borsa di studio",
        parse_confidence="high",
    )
    row_b = PositionRow(
        detail_id="x",
        position_row_index=2,
        contract_type="Borsa di studio",
        parse_confidence="high",
    )

    rows, decision = reconcile_rows(rows=[row_a, row_b], detail_id="x", numero_posti_html=1)

    assert [row.position_row_index for row in rows] == [2]
    assert decision.applied is True
    assert decision.reason_code == "applied_numero_posti_singleton_guard"
