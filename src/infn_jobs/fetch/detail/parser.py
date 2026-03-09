"""Parse INFN job detail pages into CallRaw objects."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from infn_jobs.config.settings import BASE_URL
from infn_jobs.domain.call import CallRaw

logger = logging.getLogger(__name__)

_ORIGIN = urlparse(BASE_URL).scheme + "://" + urlparse(BASE_URL).netloc


def _resolve_url(href: str) -> str:
    """Resolve a relative or absolute href to a full URL using BASE_URL origin."""
    if href.startswith("http"):
        return href
    return _ORIGIN + ("" if href.startswith("/") else "/") + href


def _find_field(tbody: BeautifulSoup, label: str) -> str | None:
    """Return the text of the <td> adjacent to a <th> matching label, or None."""
    for tr in tbody.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if th and td and th.get_text(strip=True) == label:
            return td.get_text(strip=True) or None
    return None


def parse_detail(html: bytes, detail_id: str) -> CallRaw:
    """Parse a detail page and return a CallRaw with all available fields."""
    soup = BeautifulSoup(html, "lxml")
    call = CallRaw()
    call.detail_id = detail_id
    call.detail_url = f"{BASE_URL}/dettagli_job.php?id={detail_id}"

    table = soup.find("table")
    if table is None:
        logger.warning("detail_id=%s: no table found on detail page", detail_id)
        return call

    tbody = table.find("tbody") or table

    call.numero = _find_field(tbody, "Numero")
    call.anno = _find_field(tbody, "Anno")
    call.titolo = _find_field(tbody, "Titolo")
    call.data_bando = _find_field(tbody, "Data bando")
    call.data_scadenza = _find_field(tbody, "Data scadenza")

    # Numero posti — parse as int, None if absent or non-numeric
    posti_raw = _find_field(tbody, "Numero posti")
    if posti_raw is not None:
        try:
            call.numero_posti_html = int(posti_raw)
        except ValueError:
            logger.warning("detail_id=%s: cannot parse Numero posti %r", detail_id, posti_raw)

    # PDF URL — resolve relative href to absolute
    for tr in tbody.find_all("tr"):
        th = tr.find("th")
        if th and th.get_text(strip=True) == "Bando (PDF)":
            link = tr.find("a", href=True)
            if link:
                call.pdf_url = _resolve_url(link["href"])
            break

    return call
