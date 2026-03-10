"""Read helpers for calls_raw discovery flows."""

from __future__ import annotations

import sqlite3

from infn_jobs.domain.call import CallRaw

_CALLS_RAW_COLUMNS = (
    "detail_id",
    "source_tipo",
    "listing_status",
    "numero",
    "anno",
    "titolo",
    "pdf_call_title",
    "numero_posti_html",
    "data_bando",
    "data_scadenza",
    "detail_url",
    "pdf_url",
    "pdf_cache_path",
    "pdf_fetch_status",
    "first_seen_at",
    "last_synced_at",
)
_CALLS_RAW_SELECT = f"SELECT {', '.join(_CALLS_RAW_COLUMNS)} FROM calls_raw"


def _row_to_call_raw(row: tuple[object, ...]) -> CallRaw:
    (
        detail_id,
        source_tipo,
        listing_status,
        numero,
        anno,
        titolo,
        pdf_call_title,
        numero_posti_html,
        data_bando,
        data_scadenza,
        detail_url,
        pdf_url,
        pdf_cache_path,
        pdf_fetch_status,
        first_seen_at,
        last_synced_at,
    ) = row
    return CallRaw(
        detail_id=detail_id,
        source_tipo=source_tipo,
        listing_status=listing_status,
        numero=numero,
        anno=anno,
        titolo=titolo,
        pdf_call_title=pdf_call_title,
        numero_posti_html=numero_posti_html,
        data_bando=data_bando,
        data_scadenza=data_scadenza,
        detail_url=detail_url,
        pdf_url=pdf_url,
        pdf_cache_path=pdf_cache_path,
        pdf_fetch_status=pdf_fetch_status,
        first_seen_at=first_seen_at,
        last_synced_at=last_synced_at,
    )


def list_calls_for_pdf_processing(conn: sqlite3.Connection) -> list[CallRaw]:
    """Return calls with detail_id set, ordered deterministically for PDF processing."""
    rows = conn.execute(
        f"{_CALLS_RAW_SELECT} WHERE detail_id IS NOT NULL ORDER BY detail_id"
    ).fetchall()
    return [_row_to_call_raw(row) for row in rows]
