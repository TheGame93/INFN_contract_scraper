"""Upsert helpers for calls_raw and position_rows tables."""

import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow


def upsert_call(conn: sqlite3.Connection, call: CallRaw) -> None:
    """Upsert a CallRaw into calls_raw. Preserves first_seen_at on update."""
    now = datetime.now(UTC).isoformat()
    first_seen = call.first_seen_at if call.first_seen_at is not None else now

    conn.execute(
        """
        INSERT INTO calls_raw (
            detail_id, source_tipo, listing_status, numero, anno, titolo,
            pdf_call_title, numero_posti_html, data_bando, data_scadenza,
            detail_url, pdf_url, pdf_cache_path, pdf_fetch_status,
            first_seen_at, last_synced_at
        ) VALUES (
            :detail_id, :source_tipo, :listing_status, :numero, :anno, :titolo,
            :pdf_call_title, :numero_posti_html, :data_bando, :data_scadenza,
            :detail_url, :pdf_url, :pdf_cache_path, :pdf_fetch_status,
            :first_seen_at, :last_synced_at
        )
        ON CONFLICT(detail_id) DO UPDATE SET
            source_tipo         = excluded.source_tipo,
            listing_status      = excluded.listing_status,
            numero              = excluded.numero,
            anno                = excluded.anno,
            titolo              = excluded.titolo,
            pdf_call_title      = excluded.pdf_call_title,
            numero_posti_html   = excluded.numero_posti_html,
            data_bando          = excluded.data_bando,
            data_scadenza       = excluded.data_scadenza,
            detail_url          = excluded.detail_url,
            pdf_url             = excluded.pdf_url,
            pdf_cache_path      = excluded.pdf_cache_path,
            pdf_fetch_status    = excluded.pdf_fetch_status,
            first_seen_at       = calls_raw.first_seen_at,
            last_synced_at      = excluded.last_synced_at
        """,
        {
            **asdict(call),
            "first_seen_at": first_seen,
            "last_synced_at": now,
        },
    )
    conn.commit()


def upsert_position_rows(conn: sqlite3.Connection, rows: list[PositionRow]) -> None:
    """Replace all position_rows for rows[0].detail_id. Deletes existing rows first."""
    if not rows:
        return

    detail_id = rows[0].detail_id
    conn.execute("DELETE FROM position_rows WHERE detail_id = ?", (detail_id,))

    for row in rows:
        conn.execute(
            """
            INSERT INTO position_rows (
                detail_id, position_row_index, text_quality,
                contract_type, contract_type_raw, contract_subtype, contract_subtype_raw,
                duration_months, duration_raw, section_structure_department,
                institute_cost_total_eur, institute_cost_yearly_eur,
                gross_income_total_eur, gross_income_yearly_eur,
                net_income_total_eur, net_income_yearly_eur, net_income_monthly_eur,
                contract_type_evidence, contract_subtype_evidence,
                duration_evidence, section_evidence,
                institute_cost_evidence, gross_income_evidence, net_income_evidence,
                parse_confidence
            ) VALUES (
                :detail_id, :position_row_index, :text_quality,
                :contract_type, :contract_type_raw, :contract_subtype, :contract_subtype_raw,
                :duration_months, :duration_raw, :section_structure_department,
                :institute_cost_total_eur, :institute_cost_yearly_eur,
                :gross_income_total_eur, :gross_income_yearly_eur,
                :net_income_total_eur, :net_income_yearly_eur, :net_income_monthly_eur,
                :contract_type_evidence, :contract_subtype_evidence,
                :duration_evidence, :section_evidence,
                :institute_cost_evidence, :gross_income_evidence, :net_income_evidence,
                :parse_confidence
            )
            """,
            asdict(row),
        )

    conn.commit()
