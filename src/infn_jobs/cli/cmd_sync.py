"""CLI command: sync — fetch all calls, extract PDFs, store in DB."""

import argparse
import sqlite3

from infn_jobs.config.settings import DB_PATH
from infn_jobs.pipeline.sync import run_sync
from infn_jobs.store.schema import init_db


def execute(args: argparse.Namespace) -> None:
    """Open DB, run full sync pipeline, close DB."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        run_sync(conn, dry_run=args.dry_run, force_refetch=args.force_refetch)
    finally:
        conn.close()
