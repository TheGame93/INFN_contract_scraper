"""Pipeline sync command: full idempotent fetch → extract → store loop."""

import logging
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from infn_jobs.config.settings import PDF_CACHE_DIR, TIPOS, init_data_dirs
from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.row_builder import build_rows
from infn_jobs.extract.pdf.downloader import download
from infn_jobs.extract.pdf.mutool import extract_text
from infn_jobs.fetch.client import get_session
from infn_jobs.fetch.orchestrator import fetch_all_calls
from infn_jobs.pipeline.row_reconciliation import reconcile_rows
from infn_jobs.store.export.curate import rebuild_curated
from infn_jobs.store.read import list_calls_for_pdf_processing
from infn_jobs.store.upsert import upsert_call, upsert_position_rows

logger = logging.getLogger(__name__)
runtime_logger = logging.getLogger("infn_jobs.runtime.sync")
_THROTTLE_REMINDER = (
    "If you observed 429, 503, or timeout errors, temporarily increase request delay to 5-10s "
    "before the next scraping run."
)
_HEARTBEAT_INTERVAL = 250


@dataclass
class _SyncWorkItem:
    call: CallRaw
    pdf_path: Path | None = None
    rows: list[PositionRow] = field(default_factory=list)


def _resolve_runtime_logfile_path() -> str:
    """Return active root logfile path, or 'unknown' when no FileHandler is configured."""
    for handler in logging.getLogger().handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        base_filename = getattr(handler, "baseFilename", None)
        if base_filename:
            return str(base_filename)
    return "unknown"


def _status_counts(items: list[_SyncWorkItem]) -> dict[str, int]:
    """Return deterministic status counters for runtime summaries."""
    counts = {"ok": 0, "skipped": 0, "download_error": 0, "parse_error": 0, "other": 0}
    for item in items:
        status = item.call.pdf_fetch_status
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    return counts


def _discover_remote_calls(session: object, limit_per_tipo: int | None) -> list[CallRaw]:
    """Fetch calls from remote listing/detail pages for all TIPOS."""
    calls: list[CallRaw] = []
    for tipo in TIPOS:
        logger.info("Fetching tipo %s (active + expired)", tipo)
        if limit_per_tipo is None:
            calls.extend(fetch_all_calls(session, tipo))
        else:
            calls.extend(fetch_all_calls(session, tipo, limit_per_tipo))
    return calls


def _discover_calls(
    conn: sqlite3.Connection,
    session: object,
    source: str,
    limit_per_tipo: int | None,
) -> tuple[list[CallRaw], bool]:
    """Discover sync calls and return whether discovery came from local DB."""
    if source == "remote":
        return _discover_remote_calls(session, limit_per_tipo), False

    local_calls = list_calls_for_pdf_processing(conn)

    if source == "local":
        if not local_calls:
            raise ValueError(
                "Local source requested but calls_raw is empty. "
                "Run sync with --source remote first."
            )
        return local_calls, True

    if source == "auto":
        if local_calls:
            return local_calls, True
        logger.info("source=auto: calls_raw empty, falling back to remote discovery")
        return _discover_remote_calls(session, limit_per_tipo), False

    raise ValueError(f"Unsupported source mode: {source}")


def _find_existing_cache_path(call: CallRaw) -> tuple[Path | None, bool]:
    """Resolve preferred local cache path (stored path first, canonical fallback)."""
    if call.detail_id is None:
        return None, False

    candidates: list[Path] = []
    if call.pdf_cache_path:
        candidates.append(Path(call.pdf_cache_path))

    canonical_path = PDF_CACHE_DIR / f"{call.detail_id}.pdf"
    if not call.pdf_cache_path or Path(call.pdf_cache_path) != canonical_path:
        candidates.append(canonical_path)

    has_zero_byte = False
    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        if candidate.stat().st_size > 0:
            return candidate, has_zero_byte
        has_zero_byte = True

    return None, has_zero_byte


def _warn_orphan_cache_files(expected_detail_ids: set[str]) -> None:
    """Warn about cache files that do not map to known detail_ids for this sync run."""
    if not PDF_CACHE_DIR.exists():
        return

    for cached_pdf in PDF_CACHE_DIR.glob("*.pdf"):
        if cached_pdf.stem not in expected_detail_ids:
            logger.warning(
                "Orphan cache file %s: no matching calls_raw.detail_id, skipping",
                cached_pdf.name,
            )


def _materialize_cache_paths(
    items: list[_SyncWorkItem],
    session: object,
    source: str,
    discovered_from_local_db: bool,
    force_refetch: bool,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Phase B: resolve local cache or download PDFs according to source policy."""
    total_items = len(items)
    for processed_count, item in enumerate(items, start=1):
        try:
            call = item.call
            if call.detail_id is None:
                logger.warning("Skipping call with missing detail_id during cache materialization")
                call.pdf_fetch_status = "skipped"
                continue

            detail_id = call.detail_id
            canonical_path = PDF_CACHE_DIR / f"{detail_id}.pdf"

            # Remote discovery path always materializes through downloader.
            if not discovered_from_local_db:
                if call.pdf_url is None:
                    call.pdf_fetch_status = "skipped"
                    logger.info("PDF %s: skipped (no url)", detail_id)
                    continue

                force_download = force_refetch
                is_zero_byte_canonical = (
                    canonical_path.exists()
                    and canonical_path.is_file()
                    and canonical_path.stat().st_size == 0
                )
                if is_zero_byte_canonical:
                    logger.warning(
                        "PDF %s: zero-byte cache detected, forcing re-download",
                        detail_id,
                    )
                    force_download = True

                pdf_path = download(
                    call.pdf_url,
                    canonical_path,
                    session=session,
                    force=force_download,
                )
                if pdf_path is None:
                    call.pdf_fetch_status = "download_error"
                    logger.info("PDF %s: download_error", detail_id)
                    continue

                item.pdf_path = pdf_path
                call.pdf_cache_path = str(pdf_path)
                call.pdf_fetch_status = "ok"
                logger.info("PDF %s: cache ready", detail_id)
                continue

            # Local/auto-from-db path: prefer existing cache, then optional auto download.
            existing_cache_path, has_zero_byte_cache = _find_existing_cache_path(call)
            if existing_cache_path is not None:
                item.pdf_path = existing_cache_path
                call.pdf_cache_path = str(existing_cache_path)
                call.pdf_fetch_status = "ok"
                logger.info("PDF %s: using local cache", detail_id)
                continue

            if has_zero_byte_cache:
                logger.warning("PDF %s: zero-byte local cache detected", detail_id)

            if source == "local":
                call.pdf_fetch_status = "skipped"
                logger.warning(
                    "PDF %s: missing valid local cache; skipping due source=local",
                    detail_id,
                )
                continue

            # source=auto with local discovery: download only when cache is missing/invalid
            # and url exists.
            if call.pdf_url is None:
                call.pdf_fetch_status = "skipped"
                logger.warning(
                    "PDF %s: missing cache and no url; skipping in source=auto",
                    detail_id,
                )
                continue

            force_download = force_refetch or has_zero_byte_cache
            pdf_path = download(call.pdf_url, canonical_path, session=session, force=force_download)
            if pdf_path is None:
                call.pdf_fetch_status = "download_error"
                logger.info("PDF %s: download_error", detail_id)
                continue

            item.pdf_path = pdf_path
            call.pdf_cache_path = str(pdf_path)
            call.pdf_fetch_status = "ok"
            logger.info("PDF %s: cache ready", detail_id)
        finally:
            if progress_callback is not None:
                progress_callback(processed_count, total_items)


def _parse_materialized_pdfs(
    items: list[_SyncWorkItem],
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Phase C: parse materialized PDFs into position rows."""
    total_items = len(items)
    for processed_count, item in enumerate(items, start=1):
        try:
            if item.pdf_path is None:
                continue

            call = item.call
            if call.detail_id is None:
                continue

            detail_id = call.detail_id
            logger.info("Processing detail_id=%s", detail_id)
            anno = int(call.anno) if call.anno and call.anno.isdigit() else None

            try:
                text, text_quality_enum = extract_text(item.pdf_path)
            except RuntimeError:
                call.pdf_fetch_status = "parse_error"
                logger.info("PDF %s: parse_error", detail_id)
                continue

            text_quality = text_quality_enum.value
            parsed_rows, pdf_call_title = build_rows(text, detail_id, text_quality, anno)
            item.rows, reconciliation = reconcile_rows(
                rows=parsed_rows,
                detail_id=detail_id,
                numero_posti_html=call.numero_posti_html,
            )
            call.pdf_call_title = pdf_call_title
            call.pdf_fetch_status = "ok"
            if reconciliation.raw_rows > 1:
                logger.info(
                    "detail_id=%s: row_reconciliation reason=%s raw_rows=%d kept_rows=%d "
                    "numero_posti_html=%s",
                    detail_id,
                    reconciliation.reason_code,
                    reconciliation.raw_rows,
                    reconciliation.kept_rows,
                    reconciliation.numero_posti_html,
                )
            logger.info("detail_id=%s: %d position_rows built", detail_id, len(item.rows))
            logger.info("PDF %s: ok", detail_id)
        finally:
            if progress_callback is not None:
                progress_callback(processed_count, total_items)


def _persist_sync_results(
    conn: sqlite3.Connection,
    items: list[_SyncWorkItem],
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Phase D: persist discovered calls and parsed rows, then rebuild curated tables."""
    total_items = len(items)
    for processed_count, item in enumerate(items, start=1):
        try:
            upsert_call(conn, item.call)
            if item.rows:
                upsert_position_rows(conn, item.rows)
        finally:
            if progress_callback is not None:
                progress_callback(processed_count, total_items)

    logger.info("Rebuilding curated tables after sync")
    rebuild_curated(conn)


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
    sync_started_at = time.monotonic()
    run_outcome = "completed"
    items: list[_SyncWorkItem] = []

    runtime_logger.info(
        "Sync start: source=%s logfile=%s heartbeat_interval=%d",
        source,
        _resolve_runtime_logfile_path(),
        _HEARTBEAT_INTERVAL,
    )

    def _progress_heartbeat(processed: int, total: int) -> None:
        """Emit deterministic runtime heartbeat every fixed interval."""
        if processed % _HEARTBEAT_INTERVAL == 0:
            runtime_logger.info("Sync heartbeat: processed_contracts=%d/%d", processed, total)

    def _phase_c_heartbeat(processed: int, total: int) -> None:
        """Emit deterministic Phase C heartbeat every fixed interval."""
        if processed % _HEARTBEAT_INTERVAL == 0:
            runtime_logger.info("Phase C heartbeat: processed_contracts=%d/%d", processed, total)

    def _phase_d_heartbeat(processed: int, total: int) -> None:
        """Emit deterministic Phase D heartbeat every fixed interval."""
        if processed % _HEARTBEAT_INTERVAL == 0:
            runtime_logger.info("Phase D heartbeat: processed_contracts=%d/%d", processed, total)

    try:
        phase_started_at = time.monotonic()
        logger.info("Phase A: discover calls (source=%s)", source)
        calls, discovered_from_local_db = _discover_calls(conn, session, source, limit_per_tipo)
        expected_detail_ids = {call.detail_id for call in calls if call.detail_id is not None}
        # Include existing persisted ids for remote discovery so partial fetches do not
        # mislabel valid historical cache files as orphan.
        if not discovered_from_local_db and isinstance(conn, sqlite3.Connection):
            expected_detail_ids.update(
                call.detail_id
                for call in list_calls_for_pdf_processing(conn)
                if call.detail_id is not None
            )
        _warn_orphan_cache_files(expected_detail_ids)

        items = [_SyncWorkItem(call=call) for call in calls]
        runtime_logger.info(
            "Phase A complete: discovered_contracts=%d elapsed_s=%.2f",
            len(items),
            time.monotonic() - phase_started_at,
        )

        phase_started_at = time.monotonic()
        logger.info("Phase B: materialize cache")
        _materialize_cache_paths(
            items,
            session,
            source,
            discovered_from_local_db,
            force_refetch,
            progress_callback=_progress_heartbeat,
        )
        runtime_logger.info(
            "Phase B complete: materialized_contracts=%d elapsed_s=%.2f",
            len(items),
            time.monotonic() - phase_started_at,
        )

        if download_only:
            logger.info("download_only=True: skipping parse and DB writes")
            runtime_logger.info(
                "Phase C complete: skipped=True reason=download_only elapsed_s=0.00"
            )
            runtime_logger.info(
                "Phase D complete: skipped=True reason=download_only elapsed_s=0.00"
            )
            return

        phase_started_at = time.monotonic()
        logger.info("Phase C: parse materialized PDFs")
        _parse_materialized_pdfs(items, progress_callback=_phase_c_heartbeat)
        runtime_logger.info(
            "Phase C complete: parsed_contracts=%d elapsed_s=%.2f",
            len(items),
            time.monotonic() - phase_started_at,
        )

        if dry_run:
            logger.info("dry_run=True: skipping DB writes and curated rebuild")
            runtime_logger.info("Phase D complete: skipped=True reason=dry_run elapsed_s=0.00")
            return

        phase_started_at = time.monotonic()
        logger.info("Phase D: persist calls and rows")
        _persist_sync_results(conn, items, progress_callback=_phase_d_heartbeat)
        runtime_logger.info(
            "Phase D complete: persisted_contracts=%d elapsed_s=%.2f",
            len(items),
            time.monotonic() - phase_started_at,
        )
    except KeyboardInterrupt:
        run_outcome = "interrupted"
        raise
    except Exception:
        run_outcome = "failed"
        raise
    finally:
        counts = _status_counts(items)
        runtime_logger.info(
            "Sync summary: status=%s partial_run=%s processed_contracts=%d ok=%d skipped=%d "
            "download_error=%d parse_error=%d other=%d total_elapsed_s=%.2f",
            run_outcome,
            "true" if run_outcome == "interrupted" else "false",
            len(items),
            counts["ok"],
            counts["skipped"],
            counts["download_error"],
            counts["parse_error"],
            counts["other"],
            time.monotonic() - sync_started_at,
        )
        logger.info("Throttle reminder: %s", _THROTTLE_REMINDER)
