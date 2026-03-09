"""Shared pytest fixtures for the INFN Jobs Scraper test suite."""

import sqlite3
from pathlib import Path

import pytest

from infn_jobs.store.schema import init_db


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Yield an in-memory (or tmp-file) SQLite connection with all tables created."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    init_db(conn)
    yield conn
    conn.close()
