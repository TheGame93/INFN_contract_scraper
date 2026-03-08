"""CallRaw dataclass representing one scraped job call (listing + detail fields)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CallRaw:
    """All fields scraped for a single INFN job call; every field is nullable."""

    detail_id: str | None = None
    source_tipo: str | None = None
    listing_status: str | None = None
    numero: str | None = None
    anno: str | None = None
    titolo: str | None = None
    pdf_call_title: str | None = None
    numero_posti_html: int | None = None
    data_bando: str | None = None
    data_scadenza: str | None = None
    detail_url: str | None = None
    pdf_url: str | None = None
    pdf_cache_path: str | None = None
    pdf_fetch_status: str | None = None
    first_seen_at: str | None = None
    last_synced_at: str | None = None
