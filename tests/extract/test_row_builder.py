"""Tests for the row builder."""

from dataclasses import asdict
from pathlib import Path

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse import row_builder as row_builder_module
from infn_jobs.extract.parse.core.models import ParseResult
from infn_jobs.extract.parse.fields.confidence import score_confidence
from infn_jobs.extract.parse.row_builder import build_rows
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_build_rows_single_contract_returns_one_row():
    rows, _ = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    assert len(rows) == 1


def test_build_rows_multi_same_type_returns_multiple_rows():
    rows, _ = build_rows(_read("multi_same_type.txt"), "test-2", "digital", 2022)
    assert len(rows) == 2


def test_build_rows_returns_pdf_call_title():
    _, title = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    assert title is None or isinstance(title, str)


def test_build_rows_no_text_returns_empty():
    rows, title = build_rows("", "test-1", "no_text", 2022)
    assert rows == []
    assert title is None


def test_build_rows_empty_text_returns_empty():
    rows, _ = build_rows("", "test-1", "digital", 2022)
    assert rows == []


def test_build_rows_position_row_index_sequential():
    rows, _ = build_rows(_read("multi_same_type.txt"), "test-2", "digital", 2022)
    assert rows[0].position_row_index == 0
    assert rows[1].position_row_index == 1


def test_build_rows_text_quality_stored_as_string():
    rows, _ = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    assert rows[0].text_quality == "digital"


def test_build_rows_assigns_parse_confidence_from_row_outcomes():
    rows, _ = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    for row in rows:
        assert row.parse_confidence == score_confidence(row).value


def test_build_rows_row_shape_matches_position_rows_spec_order():
    rows, _ = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    assert tuple(asdict(rows[0]).keys()) == POSITION_ROWS_COLUMN_NAMES


def test_build_rows_delegates_to_parse_pipeline(monkeypatch):
    sentinel_row = PositionRow(detail_id="test-1", position_row_index=0, text_quality="digital")
    expected = ParseResult(rows=[sentinel_row], pdf_call_title="sentinel")

    def _fake_run(_request):
        return expected

    monkeypatch.setattr(row_builder_module, "run_parse_pipeline", _fake_run)
    rows, title = build_rows("input", "test-1", "digital", 2022)

    assert rows == [sentinel_row]
    assert title == "sentinel"


def test_build_rows_4116_uses_deterministic_three_row_segmentation():
    text = Path("tests/fixtures/pdf_text/regression/detail_4116.txt").read_text(encoding="utf-8")
    rows, _ = build_rows(text, "4116", "ocr_clean", 2024)
    assert len(rows) == 3
