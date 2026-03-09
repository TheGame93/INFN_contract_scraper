"""Cache-aware PDF downloader."""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path

import requests

from infn_jobs.config.settings import RATE_LIMIT_JITTER_MAX, RATE_LIMIT_JITTER_MIN, USER_AGENT

logger = logging.getLogger(__name__)
_PRESSURE_STATUS_CODES = {429, 503}
_PRESSURE_GUIDANCE = (
    "Temporary recommendation: increase request delay to 5-10s for the next run."
)


def _sleep_with_jitter() -> None:
    time.sleep(random.uniform(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX))


def _status_code_from_error(exc: requests.RequestException) -> int | None:
    """Return HTTP status code from a requests exception when available."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code
    return None


def _is_pressure_signal(exc: requests.RequestException) -> bool:
    """Return True when exception indicates server pressure or network timeout."""
    status_code = _status_code_from_error(exc)
    return isinstance(exc, requests.Timeout) or status_code in _PRESSURE_STATUS_CODES


def download(
    url: str | None,
    dest: Path,
    session: requests.Session | None = None,
    force: bool = False,
) -> Path | None:
    """Download PDF to dest. Returns dest on success, None if url is None."""
    if not url:
        return None

    if dest.exists() and not force:
        logger.debug("PDF %s: cache hit, skipping download", dest.name)
        return dest

    _session = session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": USER_AGENT})

    dest.parent.mkdir(parents=True, exist_ok=True)
    _sleep_with_jitter()

    try:
        response = _session.get(url)
        response.raise_for_status()
    except requests.RequestException as exc:
        status_code = _status_code_from_error(exc)
        if _is_pressure_signal(exc):
            signal = "timeout" if isinstance(exc, requests.Timeout) else f"status={status_code}"
            logger.warning(
                "PDF %s: pressure signal (%s): %s. %s",
                dest.name,
                signal,
                exc,
                _PRESSURE_GUIDANCE,
            )
        else:
            logger.warning("PDF %s: error downloading: %s", dest.name, exc)
        return None

    dest.write_bytes(response.content)
    logger.info("PDF %s: downloaded", dest.name)
    return dest
