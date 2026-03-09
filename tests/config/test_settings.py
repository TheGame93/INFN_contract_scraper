"""Tests for settings module constants and enum alignment."""

from infn_jobs.config.settings import (
    RATE_LIMIT_JITTER_MAX,
    RATE_LIMIT_JITTER_MIN,
    RATE_LIMIT_SLEEP,
    TIPOS,
)
from infn_jobs.domain.enums import ContractType


def test_tipos_align_with_contract_type_enum_values():
    assert TIPOS == [ct.value for ct in ContractType]


def test_rate_limit_defaults_and_jitter_bounds():
    assert RATE_LIMIT_SLEEP == 2.5
    assert RATE_LIMIT_JITTER_MIN == 2.0
    assert RATE_LIMIT_JITTER_MAX == 3.0
    assert RATE_LIMIT_JITTER_MIN <= RATE_LIMIT_SLEEP <= RATE_LIMIT_JITTER_MAX
