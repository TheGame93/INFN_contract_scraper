"""SQLite schema: init_db creates all tables and views. Idempotent."""

import sqlite3

_CREATE_CALLS_RAW = """
CREATE TABLE IF NOT EXISTS calls_raw (
    detail_id           TEXT PRIMARY KEY,
    source_tipo         TEXT,
    listing_status      TEXT,
    numero              TEXT,
    anno                TEXT,
    titolo              TEXT,
    pdf_call_title      TEXT,
    numero_posti_html   INTEGER,
    data_bando          TEXT,
    data_scadenza       TEXT,
    detail_url          TEXT,
    pdf_url             TEXT,
    pdf_cache_path      TEXT,
    pdf_fetch_status    TEXT,
    first_seen_at       TEXT,
    last_synced_at      TEXT
)
"""

_CREATE_CALLS_CURATED = """
CREATE TABLE IF NOT EXISTS calls_curated (
    detail_id           TEXT PRIMARY KEY,
    source_tipo         TEXT,
    listing_status      TEXT,
    numero              TEXT,
    anno                TEXT,
    titolo              TEXT,
    pdf_call_title      TEXT,
    numero_posti_html   INTEGER,
    data_bando          TEXT,
    data_scadenza       TEXT,
    detail_url          TEXT,
    pdf_url             TEXT,
    pdf_cache_path      TEXT,
    pdf_fetch_status    TEXT,
    first_seen_at       TEXT,
    last_synced_at      TEXT
)
"""

_CREATE_POSITION_ROWS = """
CREATE TABLE IF NOT EXISTS position_rows (
    detail_id                       TEXT,
    position_row_index              INTEGER,
    text_quality                    TEXT,
    contract_type                   TEXT,
    contract_type_raw               TEXT,
    contract_subtype                TEXT,
    contract_subtype_raw            TEXT,
    duration_months                 INTEGER,
    duration_raw                    TEXT,
    section_structure_department    TEXT,
    institute_cost_total_eur        REAL,
    institute_cost_yearly_eur       REAL,
    gross_income_total_eur          REAL,
    gross_income_yearly_eur         REAL,
    net_income_total_eur            REAL,
    net_income_yearly_eur           REAL,
    net_income_monthly_eur          REAL,
    contract_type_evidence          TEXT,
    contract_subtype_evidence       TEXT,
    duration_evidence               TEXT,
    section_evidence                TEXT,
    institute_cost_evidence         TEXT,
    gross_income_evidence           TEXT,
    net_income_evidence             TEXT,
    parse_confidence                TEXT,
    PRIMARY KEY (detail_id, position_row_index),
    FOREIGN KEY (detail_id) REFERENCES calls_raw(detail_id)
)
"""

_CREATE_POSITION_ROWS_CURATED_VIEW = """
CREATE VIEW IF NOT EXISTS position_rows_curated AS
SELECT
    -- linkage / status
    pr.detail_id,
    pr.position_row_index,
    c.source_tipo,
    c.listing_status,
    -- call metadata (from HTML)
    c.numero,
    c.anno,
    c.numero_posti_html,
    c.data_bando,
    c.data_scadenza,
    c.first_seen_at,
    c.last_synced_at,
    c.pdf_fetch_status,
    -- source refs
    c.detail_url,
    c.pdf_url,
    c.pdf_cache_path,
    -- derived call title
    COALESCE(c.pdf_call_title, c.titolo) AS call_title,
    -- analytics fields (from PDF)
    pr.text_quality,
    pr.contract_type,
    pr.contract_type_raw,
    pr.contract_subtype,
    pr.contract_subtype_raw,
    pr.duration_months,
    pr.duration_raw,
    pr.section_structure_department,
    pr.institute_cost_total_eur,
    pr.institute_cost_yearly_eur,
    pr.gross_income_total_eur,
    pr.gross_income_yearly_eur,
    pr.net_income_total_eur,
    pr.net_income_yearly_eur,
    pr.net_income_monthly_eur,
    -- evidence
    pr.contract_type_evidence,
    pr.contract_subtype_evidence,
    pr.duration_evidence,
    pr.section_evidence,
    pr.institute_cost_evidence,
    pr.gross_income_evidence,
    pr.net_income_evidence,
    -- quality
    pr.parse_confidence
FROM position_rows pr
JOIN calls_curated c ON pr.detail_id = c.detail_id
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Create 3 tables and 1 view with IF NOT EXISTS. Idempotent."""
    conn.execute(_CREATE_CALLS_RAW)
    conn.execute(_CREATE_CALLS_CURATED)
    conn.execute(_CREATE_POSITION_ROWS)
    conn.execute(_CREATE_POSITION_ROWS_CURATED_VIEW)
