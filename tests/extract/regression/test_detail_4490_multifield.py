"""Regression lock for detail_id=4490 subtype extraction."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.row_builder import build_rows

_FIXTURE = Path("tests/fixtures/pdf_text/canary/detail_4490.txt")


def test_detail_4490_subtype_is_fascia_1_with_evidence() -> None:
    """detail_id=4490 should expose Fascia 1 subtype with anchored evidence text."""
    text = _FIXTURE.read_text(encoding="utf-8")
    rows, _pdf_call_title = build_rows(text, "4490", "ocr_clean", 2026)

    assert len(rows) == 1
    row = rows[0]
    assert row.contract_type == "Incarico di ricerca"
    assert row.contract_subtype == "Fascia 1"
    assert row.contract_subtype_raw == "Fascia 1"
    assert row.contract_subtype_evidence is not None
    assert "Fascia 1" in row.contract_subtype_evidence


def test_detail_4490_financial_fields_are_extracted_with_evidence() -> None:
    """detail_id=4490 should expose institute total and gross yearly amounts."""
    text = _FIXTURE.read_text(encoding="utf-8")
    rows, _pdf_call_title = build_rows(text, "4490", "ocr_clean", 2026)

    assert len(rows) == 1
    row = rows[0]
    assert row.institute_cost_total_eur == 27819.0
    assert row.gross_income_yearly_eur == 22500.0
    assert row.institute_cost_evidence is not None
    assert "27.819,00" in row.institute_cost_evidence
    assert row.gross_income_evidence is not None
    assert "22.500,00" in row.gross_income_evidence
