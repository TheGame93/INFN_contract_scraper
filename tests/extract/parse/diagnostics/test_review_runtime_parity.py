"""Parity tests between runtime parse output and review-mode artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from infn_jobs.extract.parse.core.models import ParseRequest
from infn_jobs.extract.parse.core.orchestrator import run_parse_pipeline
from infn_jobs.extract.parse.diagnostics.review_mode import build_review_report

_FIXTURES = Path("tests/fixtures/pdf_text")
_CASES = [
    ("single_contract.txt", "digital", 2022),
    ("ocr_clean.txt", "ocr_clean", 2022),
    ("canary/detail_4358.txt", "ocr_clean", 2025),
]


def _read(relative_path: str) -> str:
    """Return fixture text content for one relative fixture path."""
    return (_FIXTURES / relative_path).read_text(encoding="utf-8")


def _runtime_projection(text: str, detail_id: str, text_quality: str, anno: int) -> tuple:
    """Return runtime parse projection used for review/runtime parity checks."""
    runtime = run_parse_pipeline(
        ParseRequest(text=text, detail_id=detail_id, text_quality=text_quality, anno=anno)
    )
    rows_projection = tuple(
        {
            "contract_type": row.contract_type,
            "contract_subtype": row.contract_subtype,
            "duration_months": row.duration_months,
            "section_structure_department": row.section_structure_department,
            "gross_income_yearly_eur": row.gross_income_yearly_eur,
        }
        for row in runtime.rows
    )
    return runtime.pdf_call_title, rows_projection


def _review_projection(text: str, detail_id: str, text_quality: str, anno: int) -> tuple:
    """Return review-mode projection used for review/runtime parity checks."""
    review = build_review_report(
        text=text,
        detail_id=detail_id,
        text_quality=text_quality,
        anno=anno,
    )
    segments_projection = tuple(
        {
            "contract_type": segment.contract_type,
            "contract_subtype": segment.contract_subtype,
            "duration_months": segment.duration_months,
            "section_structure_department": segment.section_structure_department,
            "gross_income_yearly_eur": segment.gross_income_yearly_eur,
        }
        for segment in review.segments
    )
    return review.pdf_call_title, segments_projection, review


@pytest.mark.parametrize(("fixture_path", "text_quality", "anno"), _CASES)
def test_review_report_matches_runtime_projection(
    fixture_path: str,
    text_quality: str,
    anno: int,
) -> None:
    """Review-mode and runtime parser should agree on shared extracted outputs."""
    text = _read(fixture_path)
    detail_id = fixture_path.replace("/", "-").replace(".txt", "")

    runtime_title, runtime_rows = _runtime_projection(text, detail_id, text_quality, anno)
    review_title, review_segments, _ = _review_projection(text, detail_id, text_quality, anno)

    assert runtime_title == review_title
    assert runtime_rows == review_segments


@pytest.mark.parametrize(("fixture_path", "text_quality", "anno"), _CASES)
def test_review_report_exposes_contract_type_winner_rule(
    fixture_path: str,
    text_quality: str,
    anno: int,
) -> None:
    """Each reviewed segment should include a contract-type winner rule identifier."""
    text = _read(fixture_path)
    detail_id = fixture_path.replace("/", "-").replace(".txt", "")

    _, _, review = _review_projection(text, detail_id, text_quality, anno)

    assert review.segments
    assert all(segment.winner_rule_ids.get("contract_type") for segment in review.segments)
