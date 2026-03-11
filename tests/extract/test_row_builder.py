"""Tests for the row builder."""

from dataclasses import asdict
from pathlib import Path

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


def test_build_rows_row_shape_matches_position_rows_spec_order():
    rows, _ = build_rows(_read("single_contract.txt"), "test-1", "digital", 2022)
    assert tuple(asdict(rows[0]).keys()) == POSITION_ROWS_COLUMN_NAMES
