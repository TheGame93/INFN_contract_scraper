"""Regression gate for detail_id=4447."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.row_builder import build_rows

_FIXTURE = Path("tests/fixtures/pdf_text/regression/detail_4447.txt")


def test_detail_4447_multifield_baseline() -> None:
    """detail_id=4447 must match the agreed multifield baseline snapshot."""
    text = _FIXTURE.read_text(encoding="utf-8")
    rows, pdf_call_title = build_rows(text, "4447", "ocr_clean", 2025)

    assert len(rows) == 1
    assert pdf_call_title == "Istituto Nazionale di Fisica Nucleare"

    row = rows[0]
    assert row.contract_type == "Incarico Post-Doc"
    assert row.contract_type_raw == "INCARICO POST-DOC"
    assert row.contract_subtype == "Fascia 1"
    assert row.contract_subtype_raw == "Fascia 1"
    assert row.duration_months == 24
    assert row.duration_raw == "24 mesi"
    assert row.section_structure_department == "Sezione di Firenze dell’INFN."
    assert row.institute_cost_total_eur is None
    assert row.institute_cost_yearly_eur is None
    assert row.gross_income_total_eur is None
    assert row.gross_income_yearly_eur is None
    assert row.net_income_total_eur is None
    assert row.net_income_yearly_eur is None
    assert row.net_income_monthly_eur is None
    assert row.parse_confidence == "medium"
