"""Pipeline sync command: full idempotent fetch → extract → store loop."""

import logging
import sqlite3

from infn_jobs.config.settings import PDF_CACHE_DIR, TIPOS, init_data_dirs
from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.row_builder import build_rows
from infn_jobs.extract.pdf.downloader import download
from infn_jobs.extract.pdf.mutool import extract_text
from infn_jobs.fetch.client import get_session
from infn_jobs.fetch.orchestrator import fetch_all_calls
from infn_jobs.store.export.curate import rebuild_curated
from infn_jobs.store.upsert import upsert_call, upsert_position_rows

logger = logging.getLogger(__name__)
_THROTTLE_REMINDER = (
    "If you observed 429, 503, or timeout errors, temporarily increase request delay to 5-10s "
    "before the next scraping run."
)


def run_sync(
    conn: sqlite3.Connection,
    source: str = "local",
    limit_per_tipo: int | None = None,
    download_only: bool = False,
    dry_run: bool = False,
    force_refetch: bool = False,
) -> None:
    """Full idempotent sync pipeline: fetch all calls → extract PDFs → store."""
    init_data_dirs()
    session = get_session()
    fetch_limit = limit_per_tipo if source in {"remote", "auto"} else None

    try:
        for tipo in TIPOS:
            logger.info("Fetching tipo %s (active + expired)", tipo)
            if fetch_limit is None:
                calls = fetch_all_calls(session, tipo)
            else:
                calls = fetch_all_calls(session, tipo, fetch_limit)

            for call in calls:
                logger.info("Processing detail_id=%s", call.detail_id)
                rows: list[PositionRow] = []
                anno = int(call.anno) if call.anno and call.anno.isdigit() else None
                dest = PDF_CACHE_DIR / f"{call.detail_id}.pdf"

                if call.pdf_url is None:
                    call.pdf_fetch_status = "skipped"
                    logger.info("PDF %s: skipped (no url)", call.detail_id)
                else:
                    pdf_path = download(call.pdf_url, dest, session=session, force=force_refetch)
                    if pdf_path is None:
                        call.pdf_fetch_status = "download_error"
                        logger.info("PDF %s: download_error", call.detail_id)
                    else:
                        logger.info("PDF %s: downloaded", call.detail_id)
                        try:
                            text, text_quality_enum = extract_text(pdf_path)
                        except RuntimeError:
                            call.pdf_fetch_status = "parse_error"
                            logger.info("PDF %s: parse_error", call.detail_id)
                        else:
                            tq_str = text_quality_enum.value
                            rows, pdf_call_title = build_rows(text, call.detail_id, tq_str, anno)
                            call.pdf_call_title = pdf_call_title
                            call.pdf_cache_path = str(dest)
                            call.pdf_fetch_status = "ok"
                            logger.info(
                                "detail_id=%s: %d position_rows built", call.detail_id, len(rows)
                            )
                            logger.info("PDF %s: ok", call.detail_id)

                if dry_run:
                    logger.info("dry_run=True: skipping DB writes for detail_id=%s", call.detail_id)
                else:
                    upsert_call(conn, call)
                    if rows:
                        upsert_position_rows(conn, rows)

        if not dry_run:
            logger.info("Rebuilding curated tables after sync")
            rebuild_curated(conn)
    finally:
        logger.info("Throttle reminder: %s", _THROTTLE_REMINDER)
