"""Tests for metadata field extractors."""

from infn_jobs.extract.parse.fields.metadata import (
    extract_pdf_call_title,
    extract_section_department,
)


def test_extract_pdf_call_title_returns_first_nonempty_line():
    assert extract_pdf_call_title("Title here\nOther stuff") == "Title here"


def test_extract_pdf_call_title_skips_blank_lines():
    assert extract_pdf_call_title("\n\n  \nActual title") == "Actual title"


def test_extract_pdf_call_title_empty_returns_none():
    assert extract_pdf_call_title("") is None


def test_extract_pdf_call_title_whitespace_only_returns_none():
    assert extract_pdf_call_title("   \n\n  ") is None


def test_extract_section_department_sezione():
    value, evidence = extract_section_department("Sezione di Roma 1")
    assert value == "Sezione di Roma 1"
    assert evidence is not None


def test_extract_section_department_sede():
    value, evidence = extract_section_department("Sede di Napoli")
    assert value is not None
    assert "Napoli" in value
    assert evidence is not None


def test_extract_section_department_struttura():
    value, evidence = extract_section_department("Struttura di Frascati")
    assert value is not None
    assert "Frascati" in value
    assert evidence is not None


def test_extract_section_department_no_match():
    value, evidence = extract_section_department("Nessuna corrispondenza qui")
    assert value is None
    assert evidence is None


def test_extract_section_department_prefers_first_match_line():
    value, evidence = extract_section_department(
        "Sede di Napoli\nSezione di Roma 1\nStruttura di Frascati"
    )
    assert value == "Sede di Napoli"
    assert evidence == "Sede di Napoli"
