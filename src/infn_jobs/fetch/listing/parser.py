"""Parse INFN job listing pages into row dicts."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from infn_jobs.config.settings import BASE_URL

logger = logging.getLogger(__name__)

_ORIGIN = urlparse(BASE_URL).scheme + "://" + urlparse(BASE_URL).netloc


def _extract_detail_id(href: str) -> str | None:
    """Extract the detail_id integer string from a dettagli_job.php?id=N href."""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    ids = qs.get("id")
    if ids:
        return ids[0]
    return None


def _resolve_url(href: str) -> str:
    """Resolve a relative or absolute href to a full URL."""
    if href.startswith("http"):
        return href
    return _ORIGIN + ("" if href.startswith("/") else "/") + href


def parse_rows(html: bytes) -> list[dict]:
    """Parse a listing page and return one dict per call row."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return []

    rows = []
    for tr in table.find_all("tr"):
        link = tr.find("a", href=lambda h: h and "dettagli_job.php" in h)
        if link is None:
            continue
        href = link["href"]
        detail_id = _extract_detail_id(href)
        if detail_id is None:
            logger.warning("Row has dettagli_job.php link but no id param: %s", href)
            continue
        detail_url = _resolve_url(href)
        rows.append({"detail_id": detail_id, "detail_url": detail_url})

    return rows
