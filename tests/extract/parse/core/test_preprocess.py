"""Tests for parser preprocessing with line traceability."""

from infn_jobs.extract.parse.core.preprocess import preprocess_text


def test_preprocess_normalizes_newlines_and_formfeed_with_line_map() -> None:
    """Preprocess should normalize line endings and split form-feeds deterministically."""
    result = preprocess_text("A\r\nB\x0cC\rD\n")

    assert result.normalized_text == "A\nB\nC\nD"
    assert result.source_line_map == (1, 2, 2, 3)


def test_preprocess_empty_text_returns_empty_payload() -> None:
    """Empty input should produce an empty normalized payload and line map."""
    result = preprocess_text("")
    assert result.normalized_text == ""
    assert result.source_line_map == ()

