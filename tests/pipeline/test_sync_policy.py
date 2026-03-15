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
)
from infn_jobs.store.schema import init_db


def _make_conn(tmp_path: Path) -> sqlite3.Connection:
    """Create and initialize a SQLite DB for helper-level sync tests."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    init_db(conn)
    return conn


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
