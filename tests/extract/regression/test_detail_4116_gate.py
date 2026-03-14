"""Regression gate for detail_id=4116."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.row_builder import build_rows

_FIXTURE = Path("tests/fixtures/pdf_text/regression/detail_4116.txt")


def test_detail_4116_baseline_contract_and_row_count() -> None:
    """detail_id=4116 must keep 3 Borsa rows with stable confidence baseline."""
    text = _FIXTURE.read_text(encoding="utf-8")
    rows, pdf_call_title = build_rows(text, "4116", "ocr_clean", 2024)

    assert len(rows) >= 3
    assert pdf_call_title is not None
    assert pdf_call_title.startswith("Per incoraggiare")
    assert all(row.contract_type == "Borsa di studio" for row in rows)
    assert all(row.parse_confidence == "medium" for row in rows)

    evidences = {row.contract_type_evidence for row in rows if row.contract_type_evidence}
    assert any("destinata a diplomati" in evidence for evidence in evidences)
    assert any("laureati triennali" in evidence for evidence in evidences)
    assert any("laureati magistrali" in evidence for evidence in evidences)

    for row in rows:
        assert row.duration_months is None
        assert row.institute_cost_total_eur is None
        assert row.gross_income_total_eur is None
        assert row.net_income_total_eur is None
