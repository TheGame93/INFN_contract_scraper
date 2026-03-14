"""Contract tests for the row_builder entrypoint boundary."""

from __future__ import annotations

import inspect
from pathlib import Path

from infn_jobs.domain.position import PositionRow
from infn_jobs.extract.parse.row_builder import build_rows

_FIXTURES = Path("tests/fixtures/pdf_text")


def _read_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


def test_build_rows_signature_is_pipeline_compatible() -> None:
    """build_rows signature must remain stable for pipeline callers."""
    signature = inspect.signature(build_rows)
    assert tuple(signature.parameters) == ("text", "detail_id", "text_quality", "anno")


def test_build_rows_return_shape_is_stable_tuple_contract() -> None:
    """build_rows must return `(list[PositionRow], pdf_call_title)`."""
    result = build_rows(_read_fixture("single_contract.txt"), "contract-1", "digital", 2022)

    assert isinstance(result, tuple)
    assert len(result) == 2

    rows, pdf_call_title = result
    assert isinstance(rows, list)
    assert all(isinstance(row, PositionRow) for row in rows)
    assert {row.detail_id for row in rows} == {"contract-1"}
    assert [row.position_row_index for row in rows] == list(range(len(rows)))
    assert pdf_call_title is None or isinstance(pdf_call_title, str)
