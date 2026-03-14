"""Contract-family canary regression matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from infn_jobs.extract.parse.row_builder import build_rows

_CANARY_DIR = Path("tests/fixtures/pdf_text/canary")

_CASES = [
    ("4507", 2026, "Borsa di studio", 1),
    ("4476", 2026, "Borsa di studio", 1),
    ("4490", 2026, "Incarico di ricerca", 1),
    ("4493", 2026, "Incarico di ricerca", 1),
    ("4484", 2026, "Incarico Post-Doc", 1),
    ("4456", 2025, "Contratto di ricerca", 1),
    ("4358", 2025, "Contratto di ricerca", 1),
    ("4223", 2024, "Assegno di ricerca", 1),
    ("4302", 2024, "Assegno di ricerca", 1),
]


@pytest.mark.parametrize(("detail_id", "anno", "expected_contract_type", "expected_rows"), _CASES)
def test_contract_canary_matrix(
    detail_id: str,
    anno: int,
    expected_contract_type: str,
    expected_rows: int,
) -> None:
    """Each canary fixture must preserve its expected contract-family parse output."""
    text = (_CANARY_DIR / f"detail_{detail_id}.txt").read_text(encoding="utf-8")
    rows, pdf_call_title = build_rows(text, detail_id, "ocr_clean", anno)

    assert len(rows) == expected_rows
    assert pdf_call_title
    assert all(row.contract_type == expected_contract_type for row in rows)
