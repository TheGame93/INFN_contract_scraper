"""Tests for settings module constants and enum alignment."""

from pathlib import Path

from infn_jobs.config.settings import (
    RATE_LIMIT_JITTER_MAX,
    RATE_LIMIT_JITTER_MIN,
    RATE_LIMIT_SLEEP,
    TIPOS,
    init_data_dirs,
)
from infn_jobs.domain.enums import ContractType


def test_tipos_align_with_contract_type_enum_values():
    assert TIPOS == [ct.value for ct in ContractType]


def test_rate_limit_defaults_and_jitter_bounds():
    assert RATE_LIMIT_SLEEP == 2.5
    assert RATE_LIMIT_JITTER_MIN == 2.0
    assert RATE_LIMIT_JITTER_MAX == 3.0
    assert RATE_LIMIT_JITTER_MIN <= RATE_LIMIT_SLEEP <= RATE_LIMIT_JITTER_MAX


def test_init_data_dirs_creates_cache_export_and_log_dirs(
    tmp_path: Path, monkeypatch
) -> None:
    """init_data_dirs must create PDF cache, export, and log directories."""
    monkeypatch.setattr("infn_jobs.config.settings.PDF_CACHE_DIR", tmp_path / "pdf_cache")
    monkeypatch.setattr("infn_jobs.config.settings.EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr("infn_jobs.config.settings.LOG_DIR", tmp_path / "logs")

    init_data_dirs()

    assert (tmp_path / "pdf_cache").is_dir()
    assert (tmp_path / "exports").is_dir()
    assert (tmp_path / "logs").is_dir()
