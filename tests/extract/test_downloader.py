"""Tests for the cache-aware PDF downloader."""

from pathlib import Path
from unittest.mock import Mock, patch

import requests

from infn_jobs.config.settings import RATE_LIMIT_JITTER_MAX, RATE_LIMIT_JITTER_MIN
from infn_jobs.extract.pdf.downloader import download


def test_download_returns_none_when_url_is_none(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    assert download(None, dest) is None


def test_download_request_exception_returns_none(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    session = Mock()
    session.get.side_effect = requests.ConnectionError("network down")

    with (
        patch("infn_jobs.extract.pdf.downloader.random.uniform", return_value=2.5) as jitter_mock,
        patch("infn_jobs.extract.pdf.downloader.time.sleep") as sleep_mock,
    ):
        result = download("https://jobs.dsi.infn.it/bando.pdf", dest, session=session)

    assert result is None
    assert not dest.exists()
    jitter_mock.assert_called_once_with(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX)
    sleep_mock.assert_called_once_with(2.5)


def test_download_success_writes_file_and_returns_dest(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    session = Mock()
    response = Mock()
    response.raise_for_status.return_value = None
    response.content = b"%PDF-1.4 content"
    session.get.return_value = response

    with (
        patch("infn_jobs.extract.pdf.downloader.random.uniform", return_value=2.75) as jitter_mock,
        patch("infn_jobs.extract.pdf.downloader.time.sleep") as sleep_mock,
    ):
        result = download("https://jobs.dsi.infn.it/bando.pdf", dest, session=session)

    assert result == dest
    assert dest.read_bytes() == b"%PDF-1.4 content"
    jitter_mock.assert_called_once_with(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX)
    sleep_mock.assert_called_once_with(2.75)


def test_download_cache_hit_skips_sleep_and_jitter(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    dest.write_bytes(b"cached content")
    session = Mock()

    with (
        patch("infn_jobs.extract.pdf.downloader.random.uniform") as jitter_mock,
        patch("infn_jobs.extract.pdf.downloader.time.sleep") as sleep_mock,
    ):
        result = download("https://jobs.dsi.infn.it/bando.pdf", dest, session=session)

    assert result == dest
    session.get.assert_not_called()
    jitter_mock.assert_not_called()
    sleep_mock.assert_not_called()
