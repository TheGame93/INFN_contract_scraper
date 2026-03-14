"""Assemble PositionRow list from mutool PDF text."""

from __future__ import annotations

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.core.models import ParseRequest
from infn_jobs.extract.parse.core.orchestrator import run_compat_pipeline


def build_rows(
    text: str,
    detail_id: str,
    text_quality: str,
    anno: int | None,
) -> tuple[list[PositionRow], str | None]:
    """Segment text and build PositionRow list. Second element is pdf_call_title (call-level)."""
    result = run_compat_pipeline(
        ParseRequest(
            text=text,
            detail_id=detail_id,
            text_quality=text_quality,
            anno=anno,
        )
    )
    return result.rows, result.pdf_call_title
