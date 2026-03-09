"""Tests for the listing URL builder."""

from infn_jobs.fetch.listing.url_builder import build_urls


def test_build_urls_returns_two_urls():
    result = build_urls("Borsa")
    assert len(result) == 2


def test_build_urls_active_url_has_no_scad():
    result = build_urls("Borsa")
    assert "scad" not in result[0]
    assert "tipo=Borsa" in result[0]


def test_build_urls_expired_url_has_scad():
    result = build_urls("Borsa")
    assert "scad=1" in result[1]
    assert "tipo=Borsa" in result[1]


def test_build_urls_tipo_is_url_encoded_correctly():
    result = build_urls("Incarico di ricerca")
    assert "tipo=Incarico%20di%20ricerca" in result[0]
