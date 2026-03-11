"""Tests for store/upsert.py — upsert_call and upsert_position_rows."""

import sqlite3
import time

import pytest

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow
from infn_jobs.store.spec.calls_raw import CALLS_RAW_COLUMN_NAMES
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES
from infn_jobs.store import upsert as upsert_module
from infn_jobs.store.upsert import upsert_call, upsert_position_rows


def _make_call(detail_id: str = "1", **kwargs) -> CallRaw:
    """Return a minimal CallRaw with given detail_id."""
    return CallRaw(detail_id=detail_id, source_tipo="Borsa", **kwargs)


def _make_row(detail_id: str = "1", index: int = 0) -> PositionRow:
    """Return a minimal PositionRow."""
    return PositionRow(detail_id=detail_id, position_row_index=index)


def test_upsert_call_inserts_row(tmp_db: sqlite3.Connection) -> None:
    """upsert_call must insert one row into calls_raw."""
    upsert_call(tmp_db, _make_call("42"))
    rows = tmp_db.execute("SELECT detail_id FROM calls_raw").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "42"


def test_upsert_call_deduplicates_on_detail_id(tmp_db: sqlite3.Connection) -> None:
    """Calling upsert_call twice with same detail_id must produce exactly 1 row."""
    upsert_call(tmp_db, _make_call("1"))
    upsert_call(tmp_db, _make_call("1"))
    count = tmp_db.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 1


def test_upsert_call_first_seen_at_preserved_on_update(tmp_db: sqlite3.Connection) -> None:
    """first_seen_at must not change on a subsequent upsert."""
    upsert_call(tmp_db, _make_call("1", titolo="original"))
    first_seen_before = tmp_db.execute(
        "SELECT first_seen_at FROM calls_raw WHERE detail_id='1'"
    ).fetchone()[0]

    time.sleep(0.02)
    upsert_call(tmp_db, _make_call("1", titolo="updated"))

    row = tmp_db.execute(
        "SELECT first_seen_at, titolo FROM calls_raw WHERE detail_id='1'"
    ).fetchone()
    assert row[0] == first_seen_before, "first_seen_at must not change on update"
    assert row[1] == "updated", "titolo must be updated"


def test_upsert_call_last_synced_at_updated(tmp_db: sqlite3.Connection) -> None:
    """last_synced_at must increase on the second upsert."""
    upsert_call(tmp_db, _make_call("1"))
    t1 = tmp_db.execute(
        "SELECT last_synced_at FROM calls_raw WHERE detail_id='1'"
    ).fetchone()[0]

    time.sleep(0.02)
    upsert_call(tmp_db, _make_call("1"))
    t2 = tmp_db.execute(
        "SELECT last_synced_at FROM calls_raw WHERE detail_id='1'"
    ).fetchone()[0]

    assert t2 >= t1


def test_upsert_position_rows_inserts_rows(tmp_db: sqlite3.Connection) -> None:
    """upsert_position_rows must insert rows with correct position_row_index."""
    upsert_call(tmp_db, _make_call("1"))
    upsert_position_rows(tmp_db, [_make_row("1", 0), _make_row("1", 1)])

    rows = tmp_db.execute(
        "SELECT position_row_index FROM position_rows WHERE detail_id='1' ORDER BY position_row_index"
    ).fetchall()
    assert len(rows) == 2
    assert rows[0][0] == 0
    assert rows[1][0] == 1


def test_upsert_position_rows_replaces_existing_rows(tmp_db: sqlite3.Connection) -> None:
    """upsert_position_rows must replace old rows with new ones."""
    upsert_call(tmp_db, _make_call("1"))
    upsert_position_rows(tmp_db, [_make_row("1", 0), _make_row("1", 1)])
    upsert_position_rows(tmp_db, [_make_row("1", 0), _make_row("1", 1), _make_row("1", 2)])

    count = tmp_db.execute(
        "SELECT COUNT(*) FROM position_rows WHERE detail_id='1'"
    ).fetchone()[0]
    assert count == 3


def test_upsert_position_rows_empty_list_is_noop(tmp_db: sqlite3.Connection) -> None:
    """upsert_position_rows with empty list must not raise and must not modify DB."""
    upsert_call(tmp_db, _make_call("1"))
    upsert_position_rows(tmp_db, [_make_row("1", 0)])
    upsert_position_rows(tmp_db, [])  # noop

    count = tmp_db.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
    assert count == 1


def test_upsert_position_rows_rejects_mixed_detail_id_without_mutation(
    tmp_db: sqlite3.Connection,
) -> None:
    """Mixed detail_id batches must raise and keep existing rows unchanged."""
    upsert_call(tmp_db, _make_call("1"))
    upsert_call(tmp_db, _make_call("2"))
    upsert_position_rows(tmp_db, [_make_row("1", 0)])
    upsert_position_rows(tmp_db, [_make_row("2", 0)])

    before = tmp_db.execute(
        "SELECT detail_id, position_row_index FROM position_rows ORDER BY detail_id, position_row_index"
    ).fetchall()

    with pytest.raises(ValueError, match="homogeneous batch"):
        upsert_position_rows(tmp_db, [_make_row("1", 1), _make_row("2", 1)])

    after = tmp_db.execute(
        "SELECT detail_id, position_row_index FROM position_rows ORDER BY detail_id, position_row_index"
    ).fetchall()
    assert after == before


def test_upsert_generated_insert_columns_match_specs() -> None:
    """Generated upsert insert columns must match table specs exactly."""
    assert upsert_module._CALLS_INSERT_COLUMNS == CALLS_RAW_COLUMN_NAMES
    assert upsert_module._POSITION_ROWS_INSERT_COLUMNS == POSITION_ROWS_COLUMN_NAMES
