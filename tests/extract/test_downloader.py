"""Tests for the cache-aware PDF downloader."""

from pathlib import Path
from unittest.mock import Mock, patch

import requests

from infn_jobs.extract.pdf.downloader import download


def test_download_returns_none_when_url_is_none(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    assert download(None, dest) is None


def test_download_request_exception_returns_none(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    session = Mock()
    session.get.side_effect = requests.ConnectionError("network down")

    with patch("infn_jobs.extract.pdf.downloader.time.sleep"):
        result = download("https://jobs.dsi.infn.it/bando.pdf", dest, session=session)

    assert result is None
    assert not dest.exists()


def test_download_success_writes_file_and_returns_dest(tmp_path: Path):
    dest = tmp_path / "file.pdf"
    session = Mock()
    response = Mock()
    response.raise_for_status.return_value = None
    response.content = b"%PDF-1.4 content"
    session.get.return_value = response

    with patch("infn_jobs.extract.pdf.downloader.time.sleep"):
        result = download("https://jobs.dsi.infn.it/bando.pdf", dest, session=session)

    assert result == dest
    assert dest.read_bytes() == b"%PDF-1.4 content"
