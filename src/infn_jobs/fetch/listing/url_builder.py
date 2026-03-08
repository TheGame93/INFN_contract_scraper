"""Build listing page URLs for a given tipo (active and expired)."""

from __future__ import annotations

from infn_jobs.config.settings import BASE_URL


def build_urls(tipo: str) -> list[str]:
    """Return [active_url, expired_url] for the given tipo string."""
    active = f"{BASE_URL}/index.php?tipo={tipo}"
    expired = f"{BASE_URL}/index.php?tipo={tipo}&scad=1"
    return [active, expired]
