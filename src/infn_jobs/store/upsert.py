"""Upsert helpers for calls_raw and position_rows tables."""

import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow
from infn_jobs.store.spec.calls_raw import CALLS_RAW_COLUMN_NAMES
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES
from infn_jobs.store.spec.sql_parts import comma_separated, excluded_assignments, named_placeholders

_CALLS_INSERT_COLUMNS = CALLS_RAW_COLUMN_NAMES
_CALLS_UPDATABLE_COLUMNS = tuple(
    column
    for column in CALLS_RAW_COLUMN_NAMES
    if column not in {"detail_id", "first_seen_at", "last_synced_at"}
)
_CALLS_UPDATE_ASSIGNMENTS = (
    f"{excluded_assignments(_CALLS_UPDATABLE_COLUMNS)},\n"
    "            first_seen_at = calls_raw.first_seen_at,\n"
    "            last_synced_at = excluded.last_synced_at"
)

_POSITION_ROWS_INSERT_COLUMNS = POSITION_ROWS_COLUMN_NAMES


def prune_stale_entries(conn: sqlite3.Connection, active_detail_ids: set[str]) -> int:
    """Delete calls_raw and position_rows rows whose detail_id is not in active_detail_ids.

    Returns the number of calls_raw rows deleted. If active_detail_ids is empty, does nothing
    and returns 0 (safety guard against accidental full-table wipe).
    """
    if not active_detail_ids:
        return 0

    placeholders = f"({','.join('?' * len(active_detail_ids))})"
    params = list(active_detail_ids)

    conn.execute(f"DELETE FROM position_rows WHERE detail_id NOT IN {placeholders}", params)
    cursor = conn.execute(f"DELETE FROM calls_raw WHERE detail_id NOT IN {placeholders}", params)
    conn.commit()
    return cursor.rowcount


def upsert_call(conn: sqlite3.Connection, call: CallRaw) -> None:
    """Upsert a CallRaw into calls_raw. Preserves first_seen_at on update."""
    now = datetime.now(UTC).isoformat()
    first_seen = call.first_seen_at if call.first_seen_at is not None else now

    conn.execute(
        f"""
        INSERT INTO calls_raw (
            {comma_separated(_CALLS_INSERT_COLUMNS)}
        ) VALUES (
            {named_placeholders(_CALLS_INSERT_COLUMNS)}
        )
        ON CONFLICT(detail_id) DO UPDATE SET
{_CALLS_UPDATE_ASSIGNMENTS}
        """,
        {
            **asdict(call),
            "first_seen_at": first_seen,
            "last_synced_at": now,
        },
    )
    conn.commit()


def upsert_position_rows(conn: sqlite3.Connection, rows: list[PositionRow]) -> None:
    """Replace all position_rows for one detail_id batch; reject heterogeneous batches."""
    if not rows:
        return

    detail_ids = {row.detail_id for row in rows}
    if len(detail_ids) != 1:
        raise ValueError(
            "upsert_position_rows expects a homogeneous batch with exactly one detail_id"
        )

    detail_id = rows[0].detail_id
    conn.execute("DELETE FROM position_rows WHERE detail_id = ?", (detail_id,))

    for row in rows:
        conn.execute(
            f"""
            INSERT INTO position_rows (
                {comma_separated(_POSITION_ROWS_INSERT_COLUMNS)}
            ) VALUES (
                {named_placeholders(_POSITION_ROWS_INSERT_COLUMNS)}
            )
            """,
            asdict(row),
        )

    conn.commit()
