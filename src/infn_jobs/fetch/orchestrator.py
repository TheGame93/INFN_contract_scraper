"""Fetch orchestrator: assembles CallRaw objects for one tipo from listing + detail pages."""

from __future__ import annotations

import logging
import random
import time

import requests

from infn_jobs.config.settings import RATE_LIMIT_JITTER_MAX, RATE_LIMIT_JITTER_MIN
from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import ListingStatus
from infn_jobs.fetch.detail.parser import parse_detail
from infn_jobs.fetch.listing.parser import parse_rows
from infn_jobs.fetch.listing.url_builder import build_urls

logger = logging.getLogger(__name__)


def _sleep_with_jitter() -> None:
    time.sleep(random.uniform(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX))


def fetch_all_calls(session: requests.Session, tipo: str) -> list[CallRaw]:
    """Fetch all active and expired calls for one tipo. Returns assembled CallRaw list."""
    urls = build_urls(tipo)
    statuses = [ListingStatus.ACTIVE.value, ListingStatus.EXPIRED.value]
    calls: list[CallRaw] = []

    for url, status in zip(urls, statuses):
        logger.info("Fetching tipo %s (%s)", tipo, status)
        response = session.get(url)
        response.raise_for_status()
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
                logger.warning("detail_id=%s: error fetching detail page: %s", detail_id, exc)
                continue

            call = parse_detail(detail_resp.content, detail_id)
            call.source_tipo = tipo
            call.listing_status = status
            calls.append(call)

        _sleep_with_jitter()

    return calls
