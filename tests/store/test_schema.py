"""Tests for store/schema.py — DB schema creation and idempotency."""

import sqlite3

import pytest

from infn_jobs.store.schema import init_db


def _table_names(conn: sqlite3.Connection) -> list[str]:
    """Return all table names in the DB."""
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]


def _view_names(conn: sqlite3.Connection) -> list[str]:
    """Return all view names in the DB."""
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()]


def _column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    """Return column names for a table via PRAGMA."""
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def test_init_db_creates_calls_raw_table(tmp_db: sqlite3.Connection) -> None:
    """calls_raw table must exist after init_db."""
    assert "calls_raw" in _table_names(tmp_db)


def test_init_db_creates_position_rows_table(tmp_db: sqlite3.Connection) -> None:
    """position_rows table must exist after init_db."""
    assert "position_rows" in _table_names(tmp_db)


def test_init_db_creates_calls_curated_table(tmp_db: sqlite3.Connection) -> None:
    """calls_curated table must exist after init_db."""
    assert "calls_curated" in _table_names(tmp_db)


def test_init_db_creates_position_rows_curated_view(tmp_db: sqlite3.Connection) -> None:
    """position_rows_curated must be a VIEW, not a table."""
    assert "position_rows_curated" in _view_names(tmp_db)
    assert "position_rows_curated" not in _table_names(tmp_db)


def test_init_db_idempotent(tmp_db: sqlite3.Connection) -> None:
    """Calling init_db a second time must not raise and must not change row counts."""
    init_db(tmp_db)  # second call
    assert "calls_raw" in _table_names(tmp_db)
    assert "position_rows" in _table_names(tmp_db)
    assert "calls_curated" in _table_names(tmp_db)


def test_calls_raw_has_expected_columns(tmp_db: sqlite3.Connection) -> None:
    """calls_raw must have all expected columns."""
    cols = _column_names(tmp_db, "calls_raw")
    expected = [
        "detail_id", "source_tipo", "listing_status", "numero", "anno", "titolo",
        "pdf_call_title", "numero_posti_html", "data_bando", "data_scadenza",
        "detail_url", "pdf_url", "pdf_cache_path", "pdf_fetch_status",
        "first_seen_at", "last_synced_at",
    ]
    for col in expected:
        assert col in cols, f"Missing column: {col}"


def test_position_rows_has_expected_columns(tmp_db: sqlite3.Connection) -> None:
    """position_rows must have all expected columns."""
    cols = _column_names(tmp_db, "position_rows")
    expected = [
        "detail_id", "position_row_index", "text_quality",
        "contract_type", "contract_subtype", "duration_months", "duration_raw",
        "section_structure_department",
        "institute_cost_total_eur", "institute_cost_yearly_eur",
        "gross_income_total_eur", "gross_income_yearly_eur",
        "net_income_total_eur", "net_income_yearly_eur", "net_income_monthly_eur",
        "contract_type_evidence", "contract_subtype_evidence",
        "duration_evidence", "section_evidence",
        "institute_cost_evidence", "gross_income_evidence", "net_income_evidence",
        "parse_confidence",
    ]
    for col in expected:
        assert col in cols, f"Missing column: {col}"


def test_position_rows_has_contract_type_raw_column(tmp_db: sqlite3.Connection) -> None:
    """position_rows must have a contract_type_raw column."""
    cols = _column_names(tmp_db, "position_rows")
    assert "contract_type_raw" in cols


def test_position_rows_curated_view_columns(tmp_db: sqlite3.Connection) -> None:
    """position_rows_curated VIEW must expose key columns including call_title."""
    cursor = tmp_db.execute("SELECT * FROM position_rows_curated LIMIT 0")
    col_names = [d[0] for d in cursor.description]
    for col in ("detail_id", "position_row_index", "call_title", "parse_confidence"):
        assert col in col_names, f"Missing VIEW column: {col}"
