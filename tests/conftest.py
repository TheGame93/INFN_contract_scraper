"""Shared pytest fixtures for the INFN Jobs Scraper test suite."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

# Ensure tests always import this workspace's `src/` package, even when another
# editable install is present in the active virtualenv.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

from infn_jobs.store.schema import init_db


@pytest.fixture
def tmp_db(tmp_path: Path) -> sqlite3.Connection:
    """Yield an in-memory (or tmp-file) SQLite connection with all tables created."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    init_db(conn)
    yield conn
    conn.close()
