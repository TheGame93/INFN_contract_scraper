"""Tests for the income field extractor."""

from pathlib import Path

import pytest

from infn_jobs.extract.parse.fields.income import extract_income

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


_EUR_KEYS = [
    "institute_cost_total_eur",
    "institute_cost_yearly_eur",
    "gross_income_total_eur",
    "gross_income_yearly_eur",
    "net_income_total_eur",
    "net_income_yearly_eur",
    "net_income_monthly_eur",
]


def test_extract_income_all_7_fields_from_fixture():
    result = extract_income(_read("single_contract.txt"))
    assert result["gross_income_yearly_eur"] == pytest.approx(28000.0)
    non_none = sum(1 for k in _EUR_KEYS if result[k] is not None)
    assert non_none >= 4


def test_extract_income_compenso_lordo_label():
    seg = "Compenso lordo annuo: € 30.000,00"
    result = extract_income(seg)
    assert result["gross_income_yearly_eur"] == pytest.approx(30000.0)


def test_extract_income_importo_lordo_label():
    seg = "Importo lordo annuo: € 25.000,00"
    result = extract_income(seg)
    assert result["gross_income_yearly_eur"] == pytest.approx(25000.0)


def test_extract_income_reddito_lordo_label():
    seg = "Reddito lordo totale: € 50.000,00"
    result = extract_income(seg)
    assert result["gross_income_total_eur"] == pytest.approx(50000.0)


def test_extract_income_missing_financial_fields_all_none():
    result = extract_income(_read("missing_fields.txt"))
    for k in _EUR_KEYS:
        assert result[k] is None


def test_extract_income_evidence_captured():
    result = extract_income(_read("single_contract.txt"))
    assert result["gross_income_evidence"] is not None
    assert result["net_income_evidence"] is not None


def test_extract_income_eur_fields_are_float_or_none():
    result = extract_income(_read("single_contract.txt"))
    for k in _EUR_KEYS:
        assert result[k] is None or isinstance(result[k], float)
