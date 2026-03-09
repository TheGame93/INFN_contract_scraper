"""Tests for store/export/csv_writer.py — export_all."""

import csv
import sqlite3
from pathlib import Path

import pytest

from infn_jobs.domain.call import CallRaw
from infn_jobs.store.export.curate import rebuild_curated
from infn_jobs.store.export.csv_writer import export_all
from infn_jobs.store.upsert import upsert_call


def _seed(conn: sqlite3.Connection) -> None:
    """Insert one call and rebuild curated so all 4 tables have data."""
    upsert_call(conn, CallRaw(detail_id="1", source_tipo="Borsa", titolo="Test call"))
    rebuild_curated(conn)


_EXPECTED_FILES = {
    "calls_raw.csv",
    "calls_curated.csv",
    "position_rows_raw.csv",
    "position_rows_curated.csv",
}


def test_export_all_creates_four_csv_files(
    tmp_db: sqlite3.Connection, tmp_path: Path
) -> None:
    """export_all must create exactly 4 CSV files."""
    _seed(tmp_db)
    export_all(tmp_db, tmp_path)
    created = {p.name for p in tmp_path.glob("*.csv")}
    assert _EXPECTED_FILES == created


def test_export_calls_raw_csv_nonempty(
    tmp_db: sqlite3.Connection, tmp_path: Path
) -> None:
    """calls_raw.csv must have at least 2 lines (header + 1 data row)."""
    _seed(tmp_db)
    export_all(tmp_db, tmp_path)
    lines = (tmp_path / "calls_raw.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2


def test_export_calls_raw_csv_has_call_title_column(
    tmp_db: sqlite3.Connection, tmp_path: Path
) -> None:
    """calls_raw.csv must contain a call_title column header."""
    _seed(tmp_db)
    export_all(tmp_db, tmp_path)
    with (tmp_path / "calls_raw.csv").open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert "call_title" in header


def test_export_calls_raw_csv_columns_complete(
    tmp_db: sqlite3.Connection, tmp_path: Path
) -> None:
    """calls_raw.csv must contain expected core columns."""
    _seed(tmp_db)
    export_all(tmp_db, tmp_path)
    with (tmp_path / "calls_raw.csv").open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    for col in ("detail_id", "source_tipo", "pdf_fetch_status"):
        assert col in header, f"Missing column: {col}"


def test_export_position_rows_csv_has_detail_id_and_index(
    tmp_db: sqlite3.Connection, tmp_path: Path
) -> None:
    """position_rows_raw.csv must contain detail_id and position_row_index columns."""
    _seed(tmp_db)
    export_all(tmp_db, tmp_path)
    with (tmp_path / "position_rows_raw.csv").open(encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert "detail_id" in header
    assert "position_row_index" in header
