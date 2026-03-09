"""Tests for the parse_confidence scorer."""

from infn_jobs.domain.enums import ParseConfidence
from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.fields.confidence import score_confidence


def test_score_confidence_high_with_duration_and_income():
    row = PositionRow(duration_months=12, gross_income_yearly_eur=28000.0)
    assert score_confidence(row, "digital") == ParseConfidence.HIGH


def test_score_confidence_medium_contract_type_only():
    row = PositionRow(contract_type="Borsa di studio")
    assert score_confidence(row, "digital") == ParseConfidence.MEDIUM


def test_score_confidence_low_ocr_degraded():
    row = PositionRow(contract_type="Borsa di studio", duration_months=12)
    assert score_confidence(row, "ocr_degraded") == ParseConfidence.LOW


def test_score_confidence_low_all_none_from_readable():
    row = PositionRow()
    assert score_confidence(row, "digital") == ParseConfidence.LOW


def test_score_confidence_high_requires_duration_and_eur():
    # duration present but no EUR → not HIGH
    row = PositionRow(duration_months=12)
    result = score_confidence(row, "digital")
    assert result != ParseConfidence.HIGH


def test_score_confidence_medium_no_eur_fields():
    row = PositionRow(contract_type="Contratto di ricerca", duration_months=24)
    assert score_confidence(row, "digital") == ParseConfidence.MEDIUM
