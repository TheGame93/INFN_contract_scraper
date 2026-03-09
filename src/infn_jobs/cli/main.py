"""CLI entry point: argument parser and main dispatcher."""

import argparse
import logging
import sys

from infn_jobs.cli import cmd_export, cmd_sync
from infn_jobs.config.settings import init_data_dirs

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with all subcommands registered."""
    parser = argparse.ArgumentParser(
        prog="infn_jobs",
        description="INFN Jobs Scraper — fetch, extract, and store INFN job opportunities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch and store all INFN job listings.")
    sync_parser.add_argument(
        "--source",
        choices=("local", "remote", "auto"),
        default="local",
        help="Source mode for sync discovery and cache materialization.",
    )
    sync_parser.add_argument(
        "--limit-per-tipo",
        type=int,
        default=None,
        help="Limit fetched calls per tipo (applies to remote discovery flows).",
    )
    sync_parser.add_argument(
        "--download-only",
        action="store_true",
        default=False,
        help="Discover and materialize PDF cache only; skip parse and DB writes.",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Parse only; skip DB writes.",
    )
    sync_parser.add_argument(
        "--force-refetch",
        action="store_true",
        default=False,
        help="Re-download all PDFs even if cached.",
    )
    sync_parser.set_defaults(func=cmd_sync.execute)

    export_parser = subparsers.add_parser(
        "export-csv", help="Export DB to 4 CSV files in data/exports/."
    )
    export_parser.set_defaults(func=cmd_export.execute)

    return parser


def run() -> None:
    """Configure logging, parse arguments, and dispatch to the selected subcommand."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
    init_data_dirs()
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        logging.error("Fatal error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
