"""SQLite schema: init_db creates all tables and views. Idempotent."""

import sqlite3

from infn_jobs.store.spec.calls_raw import CALLS_CURATED_SPEC, CALLS_RAW_SPEC
from infn_jobs.store.spec.position_rows import POSITION_ROWS_SPEC
from infn_jobs.store.spec.position_rows_curated import POSITION_ROWS_CURATED_VIEW_SPEC
from infn_jobs.store.spec.sql_parts import render_table_body, render_view_select_list
from infn_jobs.store.spec.types import TableSpec, ViewSpec


def _create_table_sql(spec: TableSpec) -> str:
    """Return CREATE TABLE statement generated from a TableSpec."""
    return f"CREATE TABLE IF NOT EXISTS {spec.name} (\n{render_table_body(spec)}\n)"


def _create_view_sql(spec: ViewSpec) -> str:
    """Return CREATE VIEW statement generated from a ViewSpec."""
    return (
        f"CREATE VIEW IF NOT EXISTS {spec.name} AS\n"
        f"SELECT\n{render_view_select_list(spec)}\n{spec.from_clause}"
    )


_CREATE_CALLS_RAW = _create_table_sql(CALLS_RAW_SPEC)
_CREATE_CALLS_CURATED = _create_table_sql(CALLS_CURATED_SPEC)
_CREATE_POSITION_ROWS = _create_table_sql(POSITION_ROWS_SPEC)
_CREATE_POSITION_ROWS_CURATED_VIEW = _create_view_sql(POSITION_ROWS_CURATED_VIEW_SPEC)


def init_db(conn: sqlite3.Connection) -> None:
    """Create 3 tables and 1 view with IF NOT EXISTS. Idempotent."""
    conn.execute(_CREATE_CALLS_RAW)
    conn.execute(_CREATE_CALLS_CURATED)
    conn.execute(_CREATE_POSITION_ROWS)
    conn.execute(_CREATE_POSITION_ROWS_CURATED_VIEW)
