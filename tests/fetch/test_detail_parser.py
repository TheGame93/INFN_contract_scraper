"""Tests for the detail page HTML parser."""

from pathlib import Path

from infn_jobs.domain.call import CallRaw
from infn_jobs.fetch.detail.parser import parse_detail

FIXTURES = Path("tests/fixtures/html")


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_detail_full_page_all_fields():
    result = parse_detail(_read("detail_page_full.html"), "1234")
    assert result.numero == "123/2023"
    assert result.anno == "2023"
    assert result.titolo is not None
    assert result.numero_posti_html == 1
    assert result.data_scadenza == "31-01-2023"


def test_parse_detail_full_page_pdf_url_resolved():
    result = parse_detail(_read("detail_page_full.html"), "1234")
    assert result.pdf_url is not None
    assert result.pdf_url.startswith("http")


def test_parse_detail_old_page_numero_posti_is_none():
    result = parse_detail(_read("detail_page_old.html"), "9999")
    assert result.numero_posti_html is None


def test_parse_detail_old_page_pdf_url_is_none():
    result = parse_detail(_read("detail_page_old.html"), "9999")
    assert result.pdf_url is None


def test_parse_detail_sets_detail_id():
    result = parse_detail(_read("detail_page_full.html"), "1234")
    assert result.detail_id == "1234"


def test_parse_detail_pdf_url_absolute_used_as_is():
    html = (
        b"<html><head><meta charset='utf-8'></head><body>"
        b"<table><tbody>"
        b"<tr><th>Bando (PDF)</th><td>"
        b"<a href='https://external.example.com/bando.pdf'>bando.pdf</a>"
        b"</td></tr>"
        b"</tbody></table></body></html>"
    )
    result = parse_detail(html, "999")
    assert result.pdf_url == "https://external.example.com/bando.pdf"


def test_parse_detail_returns_call_raw_instance():
    result = parse_detail(_read("detail_page_full.html"), "1234")
    assert isinstance(result, CallRaw)
