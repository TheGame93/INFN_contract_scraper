"""CLI command: export-csv — rebuild curated tables and export 4 CSV files."""

import argparse
import sqlite3

from infn_jobs.config.settings import DB_PATH, EXPORT_DIR
from infn_jobs.pipeline.export import run_export
from infn_jobs.store.schema import init_db


def execute(args: argparse.Namespace) -> None:
    """Open DB, rebuild curated tables, export 4 CSVs, close DB."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        run_export(conn, EXPORT_DIR)
    finally:
        conn.close()
