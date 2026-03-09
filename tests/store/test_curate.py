"""Tests for store/export/curate.py — rebuild_curated."""

import sqlite3

import pytest

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow
from infn_jobs.store.export.curate import rebuild_curated
from infn_jobs.store.upsert import upsert_call, upsert_position_rows


def _seed(conn: sqlite3.Connection) -> None:
    """Insert employment call + non-employment call + 2 position rows."""
    upsert_call(conn, CallRaw(detail_id="borsa1", source_tipo="Borsa", titolo="Borsa call"))
    upsert_call(conn, CallRaw(detail_id="prize1", source_tipo="Premio", titolo="Premio call"))
    upsert_position_rows(conn, [
        PositionRow(detail_id="borsa1", position_row_index=0),
        PositionRow(detail_id="borsa1", position_row_index=1),
    ])


def test_rebuild_curated_keeps_employment_calls(tmp_db: sqlite3.Connection) -> None:
    """rebuild_curated must keep the employment-like call."""
    _seed(tmp_db)
    rebuild_curated(tmp_db)
    ids = [r[0] for r in tmp_db.execute("SELECT detail_id FROM calls_curated").fetchall()]
    assert "borsa1" in ids


def test_rebuild_curated_excludes_unknown_source_tipo(tmp_db: sqlite3.Connection) -> None:
    """rebuild_curated must exclude non-employment calls."""
    _seed(tmp_db)
    rebuild_curated(tmp_db)
    ids = [r[0] for r in tmp_db.execute("SELECT detail_id FROM calls_curated").fetchall()]
    assert "prize1" not in ids


def test_rebuild_curated_populates_calls_curated(tmp_db: sqlite3.Connection) -> None:
    """calls_curated must contain exactly 1 row after rebuild."""
    _seed(tmp_db)
    rebuild_curated(tmp_db)
    count = tmp_db.execute("SELECT COUNT(*) FROM calls_curated").fetchone()[0]
    assert count == 1


def test_rebuild_curated_view_reflects_curated_calls(tmp_db: sqlite3.Connection) -> None:
    """position_rows_curated VIEW must contain exactly 2 rows (from the borsa call)."""
    _seed(tmp_db)
    rebuild_curated(tmp_db)
    count = tmp_db.execute("SELECT COUNT(*) FROM position_rows_curated").fetchone()[0]
    assert count == 2


def test_rebuild_curated_idempotent(tmp_db: sqlite3.Connection) -> None:
    """Calling rebuild_curated twice must not duplicate rows."""
    _seed(tmp_db)
    rebuild_curated(tmp_db)
    rebuild_curated(tmp_db)
    count = tmp_db.execute("SELECT COUNT(*) FROM calls_curated").fetchone()[0]
    assert count == 1
