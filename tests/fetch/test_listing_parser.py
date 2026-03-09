"""Tests for the listing HTML parser."""

from pathlib import Path

from infn_jobs.fetch.listing.parser import parse_rows

FIXTURES = Path("tests/fixtures/html")


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_rows_active_returns_two_rows():
    result = parse_rows(_read("listing_active.html"))
    assert len(result) == 2


def test_parse_rows_active_detail_ids():
    result = parse_rows(_read("listing_active.html"))
    assert result[0]["detail_id"] == "1234"
    assert result[1]["detail_id"] == "1235"


def test_parse_rows_expired_detail_ids():
    result = parse_rows(_read("listing_expired.html"))
    assert result[0]["detail_id"] == "5000"


def test_parse_rows_detail_url_is_absolute():
    for fixture in ("listing_active.html", "listing_expired.html"):
        result = parse_rows(_read(fixture))
        for row in result:
            assert row["detail_url"].startswith("http"), f"Not absolute: {row['detail_url']}"
            # Must not smash origin and path together (no leading slash bug)
            assert "://" in row["detail_url"], f"Malformed URL: {row['detail_url']}"
            parts = row["detail_url"].split("://", 1)
            assert "/" in parts[1], f"Missing path separator in URL: {row['detail_url']}"


def test_parse_rows_detail_url_correct_format():
    result = parse_rows(_read("listing_active.html"))
    assert result[0]["detail_url"] == "https://jobs.dsi.infn.it/dettagli_job.php?id=1234"
    assert result[1]["detail_url"] == "https://jobs.dsi.infn.it/dettagli_job.php?id=1235"


def test_parse_rows_empty_table_returns_empty_list():
    html = b"<html><head><meta charset='utf-8'></head><body><table><tr><th>BANDO</th></tr></table></body></html>"
    assert parse_rows(html) == []
