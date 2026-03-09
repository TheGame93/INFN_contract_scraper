"""Project-wide constants and path configuration."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.domain.enums import ContractType

BASE_URL: str = "https://jobs.dsi.infn.it"

TIPOS: list[str] = [ct.value for ct in ContractType]

_PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
DATA_DIR: Path = _PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "infn_jobs.db"
EXPORT_DIR: Path = DATA_DIR / "exports"
PDF_CACHE_DIR: Path = DATA_DIR / "pdf_cache"

RATE_LIMIT_SLEEP: float = 1.0
MAX_RETRIES: int = 3
USER_AGENT: str = "infn-jobs-scraper/1.0 (research-tool)"


def init_data_dirs() -> None:
    """Create data subdirectories if they do not exist. Idempotent."""
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
