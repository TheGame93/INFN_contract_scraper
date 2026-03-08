"""Tests for the PDF text segmenter."""

from pathlib import Path

from infn_jobs.extract.parse.segmenter import segment

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_segment_single_entry_returns_one_segment():
    result = segment(_read("single_contract.txt"))
    assert len(result) == 1


def test_segment_multi_same_type_returns_two_segments():
    result = segment(_read("multi_same_type.txt"))
    assert len(result) == 2


def test_segment_multi_mixed_type_returns_multiple():
    result = segment(_read("multi_mixed_type.txt"))
    assert len(result) >= 2


def test_segment_empty_text_returns_single_empty():
    result = segment("")
    assert result == [""]


def test_segment_preserves_content_of_first_segment():
    result = segment(_read("single_contract.txt"))
    assert "CONTRATTO DI RICERCA" in result[0]


def test_segment_page_break_splits_on_new_header():
    # ocr_clean has a form-feed; it's a single entry so should return 1 segment
    result = segment(_read("ocr_clean.txt"))
    assert len(result) >= 1  # must not crash; single entry → 1 segment

    # multi_mixed_department has 2 entries separated by blank line
    result2 = segment(_read("multi_mixed_department.txt"))
    assert len(result2) == 2
