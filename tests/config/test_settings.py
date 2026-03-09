"""Tests for settings module constants and enum alignment."""

from infn_jobs.config.settings import TIPOS
from infn_jobs.domain.enums import ContractType


def test_tipos_align_with_contract_type_enum_values():
    assert TIPOS == [ct.value for ct in ContractType]
