"""CSV export: write 4 CSV files from all DB tables and views."""

import csv
import logging
import sqlite3
from pathlib import Path

from infn_jobs.store.spec.calls_raw import CALLS_RAW_COLUMN_NAMES
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES
from infn_jobs.store.spec.position_rows_curated import POSITION_ROWS_CURATED_OUTPUT_COLUMNS
from infn_jobs.store.spec.sql_parts import comma_separated

logger = logging.getLogger(__name__)
_CALLS_SELECT_LIST = comma_separated(CALLS_RAW_COLUMN_NAMES)
_POSITION_ROWS_SELECT_LIST = comma_separated(POSITION_ROWS_COLUMN_NAMES)
_POSITION_ROWS_CURATED_SELECT_LIST = comma_separated(POSITION_ROWS_CURATED_OUTPUT_COLUMNS)


def export_all(conn: sqlite3.Connection, export_dir: Path) -> None:
    """Write 4 CSV files to export_dir from all 4 DB tables."""
    export_dir.mkdir(parents=True, exist_ok=True)

    _export_table(
        conn,
        (
            f"SELECT {_CALLS_SELECT_LIST}, COALESCE(pdf_call_title, titolo) AS call_title "
            "FROM calls_raw"
        ),
        export_dir / "calls_raw.csv",
    )
    _export_table(
        conn,
        (
            f"SELECT {_CALLS_SELECT_LIST}, COALESCE(pdf_call_title, titolo) AS call_title "
            "FROM calls_curated"
        ),
        export_dir / "calls_curated.csv",
    )
    _export_table(
        conn,
        f"SELECT {_POSITION_ROWS_SELECT_LIST} FROM position_rows",
        export_dir / "position_rows_raw.csv",
    )
    _export_table(
        conn,
        f"SELECT {_POSITION_ROWS_CURATED_SELECT_LIST} FROM position_rows_curated",
        export_dir / "position_rows_curated.csv",
    )


def _export_table(conn: sqlite3.Connection, query: str, path: Path) -> None:
    """Execute query and write results to path as CSV with UTF-8 encoding."""
    cursor = conn.execute(query)
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    logger.info("Exported %d rows to %s", len(rows), path.name)
