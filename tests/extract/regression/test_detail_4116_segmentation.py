"""Permanent segmentation guard for detail_id=4116."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.segmenter import segment

_FIXTURE = Path("tests/fixtures/pdf_text/regression/detail_4116.txt")


def test_detail_4116_segmentation_is_three_entries() -> None:
    """detail_4116 should keep exactly three segment entries."""
    text = _FIXTURE.read_text(encoding="utf-8")
    segments = segment(text)
    assert len(segments) == 3
    assert segments[0].startswith("Borsa di studio destinata a diplomati.")
    assert segments[1].startswith("Borsa di studio destinata a laureati triennali")
    assert segments[2].startswith("Borsa di studio destinata a laureati magistrali.")

