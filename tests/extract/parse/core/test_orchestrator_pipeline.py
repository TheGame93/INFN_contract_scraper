"""Tests for the core parser orchestrator entrypoint."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.core.models import ParseRequest
from infn_jobs.extract.parse.core.orchestrator import run_parse_pipeline
from infn_jobs.extract.parse.row_builder import build_rows

_FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


def test_run_parse_pipeline_matches_row_builder_outputs() -> None:
    """Parser orchestrator should preserve current row_builder outputs."""
    text = _read("single_contract.txt")
    request = ParseRequest(
        text=text,
        detail_id="compat-1",
        text_quality="digital",
        anno=2022,
    )

    parse_result = run_parse_pipeline(request)
    legacy_rows, legacy_title = build_rows(text, "compat-1", "digital", 2022)

    assert parse_result.rows == legacy_rows
    assert parse_result.pdf_call_title == legacy_title


def test_run_parse_pipeline_handles_no_text_short_circuit() -> None:
    """Parser orchestrator should return an empty result for no_text payloads."""
    request = ParseRequest(
        text="",
        detail_id="compat-2",
        text_quality="no_text",
        anno=2022,
    )
    result = run_parse_pipeline(request)
    assert result.rows == []
    assert result.pdf_call_title is None
