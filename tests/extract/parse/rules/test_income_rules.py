"""Tests for rule-driven income extraction."""

from __future__ import annotations

import pytest

from infn_jobs.extract.parse.rules.income import resolve_income


def test_resolve_income_parses_primary_labeled_amounts() -> None:
    """Income rules should parse labeled yearly and monthly amounts."""
    segment = (
        "Compenso lordo annuo: € 28.000,00\n"
        "Compenso netto mensile: € 1.800,00\n"
    )
    result = resolve_income(segment_text=segment, contract_type="Contratto di ricerca", anno=2024)
    assert result.values["gross_income_yearly_eur"] == pytest.approx(28000.0)
    assert result.values["net_income_monthly_eur"] == pytest.approx(1800.0)
    assert result.execution_results["gross_income_yearly_eur"].winner is not None
    assert result.execution_results["net_income_monthly_eur"].winner is not None


def test_resolve_income_fallback_unqualified_lordo() -> None:
    """Unqualified gross labels should map to yearly fallback deterministically."""
    result = resolve_income(segment_text="Importo lordo: euro 1.500,00")
    assert result.values["gross_income_yearly_eur"] == pytest.approx(1500.0)
    winner = result.execution_results["gross_income_yearly_eur"].winner
    assert winner is not None
    assert winner.priority_tier == "fallback"


def test_resolve_income_missing_fields_remain_null() -> None:
    """Segments without financial labels should leave all EUR fields null."""
    result = resolve_income(segment_text="Borsa di studio\nSezione di Bari\n")
    assert result.values["institute_cost_total_eur"] is None
    assert result.values["institute_cost_yearly_eur"] is None
    assert result.values["gross_income_total_eur"] is None
    assert result.values["gross_income_yearly_eur"] is None
    assert result.values["net_income_total_eur"] is None
    assert result.values["net_income_yearly_eur"] is None
    assert result.values["net_income_monthly_eur"] is None


def test_resolve_income_parses_institute_total_with_oneri_wording() -> None:
    """Institute total should parse from annuo complessivo/oneri wording."""
    segment = (
        "L'importo annuo complessivo dell’incarico di ricerca è di € 27.819,00\n"
        "comprensivo di oneri a carico dell’Istituto.\n"
    )
    result = resolve_income(segment_text=segment)
    assert result.values["institute_cost_total_eur"] == pytest.approx(27819.0)
    assert result.execution_results["institute_cost_total_eur"].winner is not None


def test_resolve_income_parses_multiline_gross_yearly_amount() -> None:
    """Gross yearly amount should parse when value is on next line."""
    segment = (
        "Al titolare sarà riconosciuto un compenso lordo annuo omnicomprensivo pari ad €\n"
        "22.500,00 in 12 mensilità.\n"
    )
    result = resolve_income(segment_text=segment)
    assert result.values["gross_income_yearly_eur"] == pytest.approx(22500.0)
    assert result.execution_results["gross_income_yearly_eur"].winner is not None


def test_resolve_income_does_not_infer_institute_total_from_oneri_only_label() -> None:
    """On its own, oneri wording without total context should not resolve institute total."""
    segment = (
        "Incentivo economico aggiuntivo di € 3.235,20.\n"
        "Comprensivo di oneri a carico dell’Istituto.\n"
    )
    result = resolve_income(segment_text=segment)
    assert result.values["institute_cost_total_eur"] is None
