"""Pipeline export command: rebuild curated tables then write CSVs."""

import logging
import sqlite3
from pathlib import Path

from infn_jobs.store.export.csv_writer import export_all as csv_export_all
from infn_jobs.store.export.curate import rebuild_curated as store_rebuild_curated

logger = logging.getLogger(__name__)


def run_export(conn: sqlite3.Connection, export_dir: Path) -> None:
    """Rebuild curated tables, then export all 4 CSVs to export_dir."""
    logger.info("Rebuilding curated tables …")
    store_rebuild_curated(conn)
    logger.info("Curated tables rebuilt.")
    csv_export_all(conn, export_dir)
    logger.info("CSV export complete.")
