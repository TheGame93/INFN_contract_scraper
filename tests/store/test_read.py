"""Tests for store/read.py call-discovery helpers."""

import sqlite3

from infn_jobs.domain.call import CallRaw
from infn_jobs.store import read as read_module
from infn_jobs.store.spec.calls_raw import CALLS_RAW_COLUMN_NAMES
from infn_jobs.store.read import list_calls_for_pdf_processing
from infn_jobs.store.upsert import upsert_call


def test_list_calls_for_pdf_processing_empty_table_returns_empty_list(
    tmp_db: sqlite3.Connection,
) -> None:
    """list_calls_for_pdf_processing must return an empty list when calls_raw has no rows."""
    assert list_calls_for_pdf_processing(tmp_db) == []


def test_list_calls_for_pdf_processing_maps_all_call_fields(
    tmp_db: sqlite3.Connection,
) -> None:
    """list_calls_for_pdf_processing must hydrate CallRaw with nullable-safe values."""
    upsert_call(
        tmp_db,
        CallRaw(
            detail_id="A-100",
            source_tipo="Borsa",
            listing_status="active",
            numero="10",
            anno="2024",
            titolo="Titolo test",
            pdf_call_title="Titolo PDF",
            numero_posti_html=2,
            data_bando="01-01-2024",
            data_scadenza="31-01-2024",
            detail_url="https://example.test/detail/A-100",
            pdf_url="https://example.test/A-100.pdf",
            pdf_cache_path="/tmp/A-100.pdf",
            pdf_fetch_status="ok",
        ),
    )

    calls = list_calls_for_pdf_processing(tmp_db)
    assert len(calls) == 1
    call = calls[0]
    assert call.detail_id == "A-100"
    assert call.source_tipo == "Borsa"
    assert call.listing_status == "active"
    assert call.numero == "10"
    assert call.anno == "2024"
    assert call.titolo == "Titolo test"
    assert call.pdf_call_title == "Titolo PDF"
    assert call.numero_posti_html == 2
    assert call.data_bando == "01-01-2024"
    assert call.data_scadenza == "31-01-2024"
    assert call.detail_url == "https://example.test/detail/A-100"
    assert call.pdf_url == "https://example.test/A-100.pdf"
    assert call.pdf_cache_path == "/tmp/A-100.pdf"
    assert call.pdf_fetch_status == "ok"
    assert call.first_seen_at is not None
    assert call.last_synced_at is not None


def test_list_calls_for_pdf_processing_is_ordered_and_null_tolerant(
    tmp_db: sqlite3.Connection,
) -> None:
    """list_calls_for_pdf_processing must order by detail_id and preserve nullable metadata."""
    upsert_call(
        tmp_db,
        CallRaw(
            detail_id="B-200",
            source_tipo="Assegno di ricerca",
            anno=None,
            pdf_url=None,
            pdf_cache_path=None,
        ),
    )
    upsert_call(
        tmp_db,
        CallRaw(
            detail_id="A-100",
            source_tipo="Contratto di Ricerca",
            anno="2019",
            pdf_url="https://example.test/A-100.pdf",
            pdf_cache_path=None,
        ),
    )
    upsert_call(
        tmp_db,
        CallRaw(
            detail_id="C-300",
            source_tipo="Incarico di ricerca",
            anno="2021",
            pdf_url=None,
            pdf_cache_path="/tmp/C-300.pdf",
        ),
    )

    calls = list_calls_for_pdf_processing(tmp_db)
    assert [call.detail_id for call in calls] == ["A-100", "B-200", "C-300"]
    assert calls[0].anno == "2019"
    assert calls[1].anno is None
    assert calls[1].pdf_url is None
    assert calls[2].pdf_cache_path == "/tmp/C-300.pdf"


def test_list_calls_for_pdf_processing_uses_spec_column_projection_order() -> None:
    """Read helper projection must match the calls_raw spec ordering exactly."""
    assert read_module._CALLS_RAW_COLUMNS == CALLS_RAW_COLUMN_NAMES
    assert read_module._CALLS_RAW_SELECT == (
        "SELECT detail_id, source_tipo, listing_status, numero, anno, titolo, pdf_call_title, "
        "numero_posti_html, data_bando, data_scadenza, detail_url, pdf_url, pdf_cache_path, "
        "pdf_fetch_status, first_seen_at, last_synced_at FROM calls_raw"
    )
