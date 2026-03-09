"""Fetch orchestrator: assembles CallRaw objects for one tipo from listing + detail pages."""

from __future__ import annotations

import logging
import random
import re
import time

import requests

from infn_jobs.config.settings import RATE_LIMIT_JITTER_MAX, RATE_LIMIT_JITTER_MIN
from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import ListingStatus
from infn_jobs.fetch.detail.parser import parse_detail
from infn_jobs.fetch.listing.parser import parse_rows
from infn_jobs.fetch.listing.url_builder import build_urls

logger = logging.getLogger(__name__)
_PRESSURE_STATUS_CODES = {429, 503}
_PRESSURE_GUIDANCE = (
    "Temporary recommendation: increase request delay to 5-10s for the next run."
)
_PRESSURE_STATUS_PATTERN = re.compile(r"\b(429|503)\b")


def _sleep_with_jitter() -> None:
    time.sleep(random.uniform(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX))


def _status_code_from_error(exc: requests.RequestException) -> int | None:
    """Return HTTP status code from a requests exception when available."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code
    # RetryError strings often contain the final status, e.g. "too many 503 error responses".
    if isinstance(exc, requests.exceptions.RetryError):
        match = _PRESSURE_STATUS_PATTERN.search(str(exc))
        if match is not None:
            return int(match.group(1))
    return None


def _is_pressure_signal(exc: requests.RequestException) -> bool:
    """Return True when exception indicates server pressure or network timeout."""
    status_code = _status_code_from_error(exc)
    return isinstance(exc, requests.Timeout) or status_code in _PRESSURE_STATUS_CODES


def _log_fetch_warning(context: str, exc: requests.RequestException) -> None:
    """Log request exceptions with extra guidance for pressure-related failures."""
    status_code = _status_code_from_error(exc)
    if _is_pressure_signal(exc):
        signal = "timeout" if isinstance(exc, requests.Timeout) else f"status={status_code}"
        logger.warning("%s: pressure signal (%s): %s. %s", context, signal, exc, _PRESSURE_GUIDANCE)
        return
    logger.warning("%s: %s", context, exc)


def fetch_all_calls(session: requests.Session, tipo: str) -> list[CallRaw]:
    """Fetch all active and expired calls for one tipo. Returns assembled CallRaw list."""
    urls = build_urls(tipo)
    statuses = [ListingStatus.ACTIVE.value, ListingStatus.EXPIRED.value]
    calls: list[CallRaw] = []

    for url, status in zip(urls, statuses):
        logger.info("Fetching tipo %s (%s)", tipo, status)
        try:
            response = session.get(url)
            response.raise_for_status()
        except requests.RequestException as exc:
            _log_fetch_warning(f"tipo={tipo} status={status}: error fetching listing page", exc)
            _sleep_with_jitter()
            continue
        rows = parse_rows(response.content)
        if not rows:
            logger.warning("tipo=%s status=%s: 0 rows at %s", tipo, status, url)

        for row in rows:
            detail_id = row["detail_id"]
            logger.info("Processing detail_id=%s", detail_id)
            _sleep_with_jitter()
            try:
                detail_resp = session.get(row["detail_url"])
                detail_resp.raise_for_status()
            except requests.RequestException as exc:
                _log_fetch_warning(f"detail_id={detail_id}: error fetching detail page", exc)
                continue

            call = parse_detail(detail_resp.content, detail_id)
            call.source_tipo = tipo
            call.listing_status = status
            calls.append(call)

        _sleep_with_jitter()

    return calls
