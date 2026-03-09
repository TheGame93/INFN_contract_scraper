"""Tests for HTTP client session configuration."""

from infn_jobs.config.settings import MAX_RETRIES, USER_AGENT
from infn_jobs.fetch.client import get_session


def test_get_session_user_agent():
    session = get_session()
    assert session.headers["User-Agent"] == USER_AGENT


def test_get_session_has_retry_adapter():
    session = get_session()
    adapter = session.get_adapter("https://example.com")
    assert adapter.max_retries.total == MAX_RETRIES
    assert set(adapter.max_retries.status_forcelist) == {500, 502, 503, 504}
    assert 429 not in adapter.max_retries.status_forcelist
    assert "GET" in adapter.max_retries.allowed_methods


def test_get_session_backoff_factor():
    session = get_session()
    adapter = session.get_adapter("https://example.com")
    assert adapter.max_retries.backoff_factor == 1.0


def test_get_session_mounts_http_and_https():
    session = get_session()
    http_adapter = session.get_adapter("http://example.com")
    https_adapter = session.get_adapter("https://example.com")
    assert http_adapter.max_retries.total == MAX_RETRIES
    assert https_adapter.max_retries.total == MAX_RETRIES
