"""Smoke tests for parser core models."""

from infn_jobs.extract.parse.core.models import ParseRequest, ParseResult


def test_parse_request_stores_input_payload() -> None:
    """ParseRequest should preserve constructor values."""
    request = ParseRequest(
        text="body",
        detail_id="abc",
        text_quality="digital",
        anno=2026,
    )

    assert request.text == "body"
    assert request.detail_id == "abc"
    assert request.text_quality == "digital"
    assert request.anno == 2026


def test_parse_result_defaults_are_empty_and_nullable() -> None:
    """ParseResult should default to empty rows and nullable title."""
    result = ParseResult()
    assert result.rows == []
    assert result.pdf_call_title is None

