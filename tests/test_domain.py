"""Smoke tests for the domain layer: enums and dataclasses."""

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import ContractType, ListingStatus, ParseConfidence, TextQuality
from infn_jobs.domain.position import PositionRow


def test_listing_status_values():
    assert ListingStatus.ACTIVE.value == "active"
    assert ListingStatus.EXPIRED.value == "expired"


def test_contract_type_values():
    assert ContractType.BORSA.value == "Borsa"
    assert ContractType.INCARICO_RICERCA.value == "Incarico di ricerca"
    assert ContractType.INCARICO_POSTDOC.value == "Incarico Post-Doc"
    assert ContractType.CONTRATTO_RICERCA.value == "Contratto di ricerca"
    assert ContractType.ASSEGNO_RICERCA.value == "Assegno di ricerca"
    assert len(ContractType) == 5


def test_parse_confidence_values():
    assert ParseConfidence.HIGH.value == "high"
    assert ParseConfidence.MEDIUM.value == "medium"
    assert ParseConfidence.LOW.value == "low"


def test_text_quality_values():
    assert TextQuality.DIGITAL.value == "digital"
    assert TextQuality.OCR_CLEAN.value == "ocr_clean"
    assert TextQuality.OCR_DEGRADED.value == "ocr_degraded"
    assert TextQuality.NO_TEXT.value == "no_text"


def test_call_raw_all_none():
    c = CallRaw()
    assert c.detail_id is None
    assert c.source_tipo is None
    assert c.listing_status is None
    assert c.numero is None
    assert c.anno is None
    assert c.titolo is None
    assert c.pdf_call_title is None
    assert c.numero_posti_html is None
    assert c.data_bando is None
    assert c.data_scadenza is None
    assert c.detail_url is None
    assert c.pdf_url is None
    assert c.pdf_cache_path is None
    assert c.pdf_fetch_status is None
    assert c.first_seen_at is None
    assert c.last_synced_at is None


def test_call_raw_with_detail_id():
    c = CallRaw(detail_id="123")
    assert c.detail_id == "123"
    assert c.source_tipo is None
    assert c.titolo is None
    assert c.last_synced_at is None


def test_call_raw_pdf_call_title_defaults_none():
    assert CallRaw().pdf_call_title is None


def test_position_row_all_none():
    r = PositionRow()
    assert r.detail_id is None
    assert r.position_row_index is None
    assert r.text_quality is None
    assert r.contract_type is None
    assert r.contract_type_raw is None
    assert r.contract_subtype is None
    assert r.contract_subtype_raw is None
    assert r.duration_months is None
    assert r.duration_raw is None
    assert r.section_structure_department is None
    assert r.institute_cost_total_eur is None
    assert r.institute_cost_yearly_eur is None
    assert r.gross_income_total_eur is None
    assert r.gross_income_yearly_eur is None
    assert r.net_income_total_eur is None
    assert r.net_income_yearly_eur is None
    assert r.net_income_monthly_eur is None
    assert r.parse_confidence is None


def test_position_row_with_index():
    r = PositionRow(detail_id="42", position_row_index=0)
    assert r.detail_id == "42"
    assert r.position_row_index == 0
    assert r.contract_type is None


def test_position_row_eur_fields_default_none():
    r = PositionRow()
    assert r.institute_cost_total_eur is None
    assert r.institute_cost_yearly_eur is None
    assert r.gross_income_total_eur is None
    assert r.gross_income_yearly_eur is None
    assert r.net_income_total_eur is None
    assert r.net_income_yearly_eur is None
    assert r.net_income_monthly_eur is None
