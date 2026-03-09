"""Cache-aware PDF downloader."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from infn_jobs.config.settings import RATE_LIMIT_SLEEP, USER_AGENT

logger = logging.getLogger(__name__)


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
    time.sleep(RATE_LIMIT_SLEEP)

    try:
        response = _session.get(url)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("PDF %s: error downloading: %s", dest.name, exc)
        return None

    dest.write_bytes(response.content)
    logger.info("PDF %s: downloaded", dest.name)
    return dest
