"""CLI command: sync — fetch all calls, extract PDFs, store in DB."""

import argparse
import sqlite3

from infn_jobs.config.settings import DB_PATH
from infn_jobs.pipeline.sync import run_sync
from infn_jobs.store.schema import init_db


def _validate_sync_args(args: argparse.Namespace) -> None:
    """Validate sync-flag combinations before opening DB connections."""
    if args.limit_per_tipo is not None and args.limit_per_tipo <= 0:
        raise ValueError("--limit-per-tipo must be a positive integer (for example: 20).")

    if args.source == "local" and args.force_refetch:
        raise ValueError(
            "--force-refetch cannot be used with --source local. "
            "Use --source remote to re-download PDFs."
        )

    if args.source == "local" and args.download_only:
        raise ValueError(
            "--download-only cannot be used with --source local. "
            "Use --source remote to build cache files from the network."
        )


def execute(args: argparse.Namespace) -> None:
    """Open DB, run full sync pipeline, close DB."""
    _validate_sync_args(args)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        run_sync(
            conn,
            source=args.source,
            limit_per_tipo=args.limit_per_tipo,
            download_only=args.download_only,
            dry_run=args.dry_run,
            force_refetch=args.force_refetch,
        )
    finally:
        conn.close()
