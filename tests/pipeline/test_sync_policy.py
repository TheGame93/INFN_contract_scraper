"""Characterization tests for sync policy helper branches."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from infn_jobs.domain.call import CallRaw
from infn_jobs.pipeline.sync import (
    _discover_calls,
    _find_existing_cache_path,
    _warn_orphan_cache_files,
)
from infn_jobs.store.schema import init_db


def _make_conn(tmp_path: Path) -> sqlite3.Connection:
    """Create and initialize a SQLite DB for helper-level sync tests."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    init_db(conn)
    return conn


def test_discover_calls_remote_uses_remote_flow(tmp_path: Path) -> None:
    """_discover_calls must use remote discovery and skip DB read for source=remote."""
    conn = _make_conn(tmp_path)
    session = object()
    remote_calls = [CallRaw(detail_id="remote-1")]

    with (
        patch("infn_jobs.pipeline.sync._discover_remote_calls", return_value=remote_calls) as remote_mock,
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing") as local_mock,
    ):
        calls, from_local = _discover_calls(conn, session, "remote", 3)

    assert calls == remote_calls
    assert from_local is False
    remote_mock.assert_called_once_with(session, 3)
    local_mock.assert_not_called()
    conn.close()


def test_discover_calls_local_requires_nonempty_db_calls(tmp_path: Path) -> None:
    """_discover_calls must return local rows for source=local and error on empty DB."""
    conn = _make_conn(tmp_path)
    local_calls = [CallRaw(detail_id="local-1")]

    with patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=local_calls):
        calls, from_local = _discover_calls(conn, object(), "local", None)

    assert calls == local_calls
    assert from_local is True

    with patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=[]):
        with pytest.raises(ValueError, match="--source remote"):
            _discover_calls(conn, object(), "local", None)
    conn.close()


def test_discover_calls_auto_prefers_local_and_falls_back_to_remote(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_discover_calls source=auto must use local calls first, then remote fallback."""
    conn = _make_conn(tmp_path)
    local_calls = [CallRaw(detail_id="local-auto-1")]
    remote_calls = [CallRaw(detail_id="remote-auto-1")]

    with (
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=local_calls),
        patch("infn_jobs.pipeline.sync._discover_remote_calls") as remote_mock,
    ):
        calls, from_local = _discover_calls(conn, object(), "auto", 5)
    assert calls == local_calls
    assert from_local is True
    remote_mock.assert_not_called()

    caplog.clear()
    caplog.set_level("INFO")
    session = object()
    with (
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=[]),
        patch("infn_jobs.pipeline.sync._discover_remote_calls", return_value=remote_calls) as remote_mock,
    ):
        calls, from_local = _discover_calls(conn, session, "auto", 2)
    assert calls == remote_calls
    assert from_local is False
    remote_mock.assert_called_once_with(session, 2)
    assert "falling back to remote discovery" in caplog.text
    conn.close()


def test_discover_calls_rejects_unsupported_source(tmp_path: Path) -> None:
    """_discover_calls must reject unknown source modes."""
    conn = _make_conn(tmp_path)
    with pytest.raises(ValueError, match="Unsupported source mode"):
        _discover_calls(conn, object(), "invalid", None)
    conn.close()


def test_find_existing_cache_path_prefers_stored_path(tmp_path: Path) -> None:
    """_find_existing_cache_path must prefer a valid stored path over canonical fallback."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    stored = tmp_path / "custom.pdf"
    canonical = cache_dir / "abc.pdf"
    stored.write_bytes(b"stored")
    canonical.write_bytes(b"canonical")
    call = CallRaw(detail_id="abc", pdf_cache_path=str(stored))

    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir):
        selected, has_zero_byte = _find_existing_cache_path(call)

    assert selected == stored
    assert has_zero_byte is False


def test_find_existing_cache_path_uses_canonical_when_stored_missing(tmp_path: Path) -> None:
    """_find_existing_cache_path must fall back to canonical path when stored path is missing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    canonical = cache_dir / "abc.pdf"
    canonical.write_bytes(b"canonical")
    missing_stored = tmp_path / "missing.pdf"
    call = CallRaw(detail_id="abc", pdf_cache_path=str(missing_stored))

    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir):
        selected, has_zero_byte = _find_existing_cache_path(call)

    assert selected == canonical
    assert has_zero_byte is False


def test_find_existing_cache_path_zero_byte_signaling(tmp_path: Path) -> None:
    """_find_existing_cache_path must signal zero-byte candidates even when fallback succeeds."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    zero = tmp_path / "zero.pdf"
    zero.write_bytes(b"")
    canonical = cache_dir / "abc.pdf"
    canonical.write_bytes(b"canonical")
    call = CallRaw(detail_id="abc", pdf_cache_path=str(zero))

    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir):
        selected, has_zero_byte = _find_existing_cache_path(call)

    assert selected == canonical
    assert has_zero_byte is True

    canonical.unlink()
    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir):
        selected, has_zero_byte = _find_existing_cache_path(call)

    assert selected is None
    assert has_zero_byte is True


def test_warn_orphan_cache_files_warns_only_for_orphans(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_warn_orphan_cache_files must warn only for cache PDFs outside expected ids."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "known.pdf").write_bytes(b"known")
    (cache_dir / "orphan.pdf").write_bytes(b"orphan")
    (cache_dir / "ignore.txt").write_text("not-a-pdf", encoding="utf-8")

    caplog.set_level("WARNING")
    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir):
        _warn_orphan_cache_files({"known"})

    warnings = [rec.getMessage() for rec in caplog.records]
    assert len(warnings) == 1
    assert "orphan.pdf" in warnings[0]


def test_warn_orphan_cache_files_noop_when_cache_dir_missing(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_warn_orphan_cache_files must not warn when cache directory does not exist."""
    missing_cache_dir = tmp_path / "missing-cache"

    caplog.set_level("WARNING")
    with patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", missing_cache_dir):
        _warn_orphan_cache_files(set())

    assert caplog.records == []
