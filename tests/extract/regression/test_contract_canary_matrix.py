"""Contract-family canary regression matrix."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from infn_jobs.extract.parse.row_builder import build_rows

_CANARY_DIR = Path("tests/fixtures/pdf_text/canary")
_PROVENANCE_MANIFEST = Path("docs/regressions/canary_provenance.md")
_PROVENANCE_ROW_RE = re.compile(r"^\|\s*`(?P<detail_id>\d+)`\s*\|\s*`(?P<fixture_path>[^`]+)`")

_CASES = [
    ("4507", 2026, "Borsa di studio", 1),
    ("4476", 2026, "Borsa di studio", 1),
    ("4490", 2026, "Incarico di ricerca", 1),
    ("4493", 2026, "Incarico di ricerca", 1),
    ("4484", 2026, "Incarico Post-Doc", 1),
    ("4456", 2025, "Contratto di ricerca", 1),
    ("4358", 2025, "Contratto di ricerca", 1),
    ("4441", 2025, "Contratto di ricerca", 2),  # oversegmentation canary: 2 raw rows, 1 posti
    ("4458", 2025, "Contratto di ricerca", 2),  # oversegmentation canary: 2 raw rows, 1 posti
    ("4223", 2024, "Assegno di ricerca", 1),
    ("4302", 2024, "Assegno di ricerca", 1),
]


def _manifest_rows() -> dict[str, str]:
    """Return detail_id -> fixture path mapping parsed from provenance manifest table."""
    rows: dict[str, str] = {}
    for line in _PROVENANCE_MANIFEST.read_text(encoding="utf-8").splitlines():
        match = _PROVENANCE_ROW_RE.match(line.strip())
        if match is None:
            continue
        rows[match.group("detail_id")] = match.group("fixture_path")
    return rows


def test_contract_canary_matrix_matches_provenance_manifest() -> None:
    """Canary cases should stay aligned with provenance manifest detail IDs and fixture paths."""
    manifest_rows = _manifest_rows()
    case_ids = {detail_id for detail_id, *_ in _CASES}

    assert case_ids == set(manifest_rows)
    for detail_id in case_ids:
        assert manifest_rows[detail_id] == f"tests/fixtures/pdf_text/canary/detail_{detail_id}.txt"


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
