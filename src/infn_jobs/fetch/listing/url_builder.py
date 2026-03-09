"""Build listing page URLs for a given tipo (active and expired)."""

from __future__ import annotations

from urllib.parse import quote

from infn_jobs.config.settings import BASE_URL


def build_urls(tipo: str) -> list[str]:
    """Return [active_url, expired_url] for the given tipo string."""
    tipo_encoded = quote(tipo, safe="")
    active = f"{BASE_URL}/index.php?tipo={tipo_encoded}"
    expired = f"{BASE_URL}/index.php?tipo={tipo_encoded}&scad=1"
    return [active, expired]
