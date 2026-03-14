"""Tests for deterministic core segmentation."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed

_FIXTURES = Path("tests/fixtures/pdf_text")
_REGRESSION = Path("tests/fixtures/pdf_text/regression")


def test_segment_preprocessed_splits_multi_entry_fixture() -> None:
    """Core segmentation should split known multi-entry fixtures."""
    text = (_FIXTURES / "multi_same_type.txt").read_text(encoding="utf-8")
    spans = segment_preprocessed(preprocess_text(text))
    assert len(spans) == 2
    assert all(span.source_line_start is not None for span in spans)


def test_segment_preprocessed_uses_lowercase_fallback_when_needed() -> None:
    """Lowercase-only headers should still split via fallback candidate starts."""
    text = (
        "borsa di studio - n. 1\n"
        "Dettaglio 1.\n"
        "borsa di studio - n. 2\n"
        "Dettaglio 2.\n"
    )
    spans = segment_preprocessed(preprocess_text(text))
    assert len(spans) == 2


def test_segment_preprocessed_4116_does_not_oversplit_inline_mentions() -> None:
    """detail_4116 should split into 3 meaningful segments."""
    text = (_REGRESSION / "detail_4116.txt").read_text(encoding="utf-8")
    spans = segment_preprocessed(preprocess_text(text))
    assert len(spans) == 3

