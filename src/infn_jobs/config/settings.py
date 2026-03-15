"""Project-wide constants and path configuration."""

from __future__ import annotations

from pathlib import Path

from infn_jobs.domain.enums import ContractType

BASE_URL: str = "https://jobs.dsi.infn.it"

TIPOS: list[str] = [ct.value for ct in ContractType]

PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "infn_jobs.db"
EXPORT_DIR: Path = DATA_DIR / "exports"
PDF_CACHE_DIR: Path = DATA_DIR / "pdf_cache"
LOG_DIR: Path = DATA_DIR / "logs"

RATE_LIMIT_JITTER_MIN: float = 2.0
RATE_LIMIT_JITTER_MAX: float = 3.0
RATE_LIMIT_SLEEP: float = 2.5
MAX_RETRIES: int = 3
USER_AGENT: str = "infn-jobs-scraper/1.0 (research-tool)"


def init_data_dirs() -> None:
    """Create data subdirectories if they do not exist. Idempotent."""
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
