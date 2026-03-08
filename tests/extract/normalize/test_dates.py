"""Tests for the date parser."""

from datetime import date

from infn_jobs.extract.parse.normalize.dates import parse_date


def test_parse_date_ddmmyyyy_hyphen():
    assert parse_date("31-01-2023") == date(2023, 1, 31)


def test_parse_date_ddmmyyyy_slash():
    assert parse_date("31/01/2023") == date(2023, 1, 31)


def test_parse_date_returns_date_object():
    result = parse_date("15-06-2020")
    assert isinstance(result, date)


def test_parse_date_none_returns_none():
    assert parse_date(None) is None


def test_parse_date_empty_returns_none():
    assert parse_date("") is None


def test_parse_date_invalid_date_returns_none():
    assert parse_date("32-13-2023") is None


def test_parse_date_wrong_format_returns_none():
    assert parse_date("2023-01-31") is None
