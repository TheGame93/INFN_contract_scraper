"""Integration canary for detail_id=4358 listing-vs-PDF mismatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import TextQuality
from infn_jobs.pipeline.sync import run_sync
from infn_jobs.store.upsert import upsert_call

_FIXTURE = Path("tests/fixtures/pdf_text/canary/detail_4358.txt")


def test_4358_listing_tipo_mismatch_keeps_pdf_semantics(tmp_db, tmp_path: Path) -> None:
    """PDF parsing must classify 4358 as Contratto di ricerca despite listing tipo mismatch."""
    local_pdf = tmp_path / "4358.pdf"
    local_pdf.write_bytes(b"%PDF-1.4 test")
    upsert_call(
        tmp_db,
        CallRaw(
            detail_id="4358",
            source_tipo="Assegno di ricerca",
            listing_status="expired",
            anno="2025",
            pdf_url=None,
            pdf_cache_path=str(local_pdf),
        ),
    )

    parsed_text = _FIXTURE.read_text(encoding="utf-8")
    with patch(
        "infn_jobs.pipeline.sync.extract_text",
        return_value=(parsed_text, TextQuality.OCR_CLEAN),
    ):
        run_sync(tmp_db, source="local", dry_run=False, force_refetch=False)

    source_tipo = tmp_db.execute(
        "SELECT source_tipo FROM calls_raw WHERE detail_id = '4358'"
    ).fetchone()[0]
    parsed_contract_types = {
        row[0]
        for row in tmp_db.execute(
            "SELECT contract_type FROM position_rows WHERE detail_id = '4358'"
        ).fetchall()
    }

    assert source_tipo == "Assegno di ricerca"
    assert parsed_contract_types == {"Contratto di ricerca"}
