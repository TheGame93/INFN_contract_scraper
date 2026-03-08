"""Tests for the EUR currency normalizer."""

import pytest

from infn_jobs.extract.parse.normalize.currency import normalize_eur


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("33.681,30", pytest.approx(33681.30)),
        ("1200", 1200.0),
        ("1200.50", 1200.50),
        ("€ 1.200,00", 1200.0),
        ("33.681\n,30", pytest.approx(33681.30)),
        ("1.200", 1200.0),
    ],
)
def test_normalize_eur_valid(input_str, expected):
    assert normalize_eur(input_str) == expected


def test_normalize_eur_italian_format():
    assert normalize_eur("33.681,30") == pytest.approx(33681.30)


def test_normalize_eur_plain_integer():
    assert normalize_eur("1200") == 1200.0


def test_normalize_eur_plain_decimal():
    assert normalize_eur("1200.50") == pytest.approx(1200.50)


def test_normalize_eur_with_euro_symbol():
    assert normalize_eur("€ 1.200,00") == 1200.0


def test_normalize_eur_line_broken_number():
    assert normalize_eur("33.681\n,30") == pytest.approx(33681.30)


def test_normalize_eur_thousands_only_no_cents():
    assert normalize_eur("1.200") == 1200.0


def test_normalize_eur_none_returns_none():
    assert normalize_eur(None) is None


def test_normalize_eur_empty_returns_none():
    assert normalize_eur("") is None


def test_normalize_eur_unparseable_returns_none():
    assert normalize_eur("n/d") is None
