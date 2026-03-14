"""Regression locks for section boundary extraction on canary fixtures."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.row_builder import build_rows


def _parse_canary(detail_id: str, anno: int):
    text = Path(f"tests/fixtures/pdf_text/canary/detail_{detail_id}.txt").read_text(
        encoding="utf-8"
    )
    rows, _title = build_rows(text, detail_id, "ocr_clean", anno)
    assert len(rows) == 1
    return rows[0]


def test_detail_4223_section_boundary_is_trimmed() -> None:
    """detail_id=4223 should not include trailing 'sul seguente' clause in section value."""
    row = _parse_canary("4223", 2024)
    assert row.section_structure_department == "Sezione di Ferrara dell'I.N.F.N."


def test_detail_4302_section_boundary_is_trimmed() -> None:
    """detail_id=4302 should not include trailing funding clause in section value."""
    row = _parse_canary("4302", 2024)
    assert row.section_structure_department == "Sezione di Bologna dell'I.N.F.N."
