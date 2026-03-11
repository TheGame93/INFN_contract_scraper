"""Column and table specs for calls_raw and calls_curated."""

from __future__ import annotations

from infn_jobs.store.spec.types import ColumnSpec, TableSpec

_CALLS_COLUMNS = (
    ColumnSpec("detail_id", "TEXT"),
    ColumnSpec("source_tipo", "TEXT"),
    ColumnSpec("listing_status", "TEXT"),
    ColumnSpec("numero", "TEXT"),
    ColumnSpec("anno", "TEXT"),
    ColumnSpec("titolo", "TEXT"),
    ColumnSpec("pdf_call_title", "TEXT"),
    ColumnSpec("numero_posti_html", "INTEGER"),
    ColumnSpec("data_bando", "TEXT"),
    ColumnSpec("data_scadenza", "TEXT"),
    ColumnSpec("detail_url", "TEXT"),
    ColumnSpec("pdf_url", "TEXT"),
    ColumnSpec("pdf_cache_path", "TEXT"),
    ColumnSpec("pdf_fetch_status", "TEXT"),
    ColumnSpec("first_seen_at", "TEXT"),
    ColumnSpec("last_synced_at", "TEXT"),
)

CALLS_RAW_SPEC = TableSpec(
    name="calls_raw",
    columns=_CALLS_COLUMNS,
    constraints=("PRIMARY KEY (detail_id)",),
)

CALLS_CURATED_SPEC = TableSpec(
    name="calls_curated",
    columns=_CALLS_COLUMNS,
    constraints=("PRIMARY KEY (detail_id)",),
)

CALLS_RAW_COLUMN_NAMES = CALLS_RAW_SPEC.column_names
CALLS_CURATED_COLUMN_NAMES = CALLS_CURATED_SPEC.column_names
