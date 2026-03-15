"""CLI entry point: argument parser and main dispatcher."""

import argparse
import datetime
import logging
import sys
from pathlib import Path

from infn_jobs.cli import cmd_export, cmd_sync
from infn_jobs.cli.update_check import maybe_handle_startup_update_check
from infn_jobs.config.settings import LOG_DIR, init_data_dirs

logger = logging.getLogger(__name__)
_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
_RUNTIME_LOGGER_PREFIX = "infn_jobs.runtime"


class _TerminalLogFilter(logging.Filter):
    """Allow only warnings/errors and runtime-status records on terminal."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True for terminal-visible records."""
        if record.levelno >= logging.WARNING:
            return True
        return record.name.startswith(_RUNTIME_LOGGER_PREFIX)


def _build_sync_logfile_path() -> Path:
    """Return one deterministic per-run logfile path under data/logs."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return LOG_DIR / f"sync_{timestamp}.log"


def _configure_logging() -> Path:
    """Configure root logging with a file sink and filtered terminal sink."""
    logfile_path = _build_sync_logfile_path()
    formatter = logging.Formatter(_LOG_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in tuple(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(logfile_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    terminal_handler = logging.StreamHandler()
    terminal_handler.setLevel(logging.INFO)
    terminal_handler.setFormatter(formatter)
    terminal_handler.addFilter(_TerminalLogFilter())

    root_logger.addHandler(file_handler)
    root_logger.addHandler(terminal_handler)
    return logfile_path


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
    if not maybe_handle_startup_update_check():
        return
    init_data_dirs()
    logfile_path = _configure_logging()
    logger.info("Detailed sync logs will be written to %s", logfile_path)
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        logging.error("Fatal error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
