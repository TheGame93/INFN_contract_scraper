"""Cross-layer consistency guards between specs and dataclasses."""

from dataclasses import fields

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.position import PositionRow
from infn_jobs.store.spec.calls_raw import CALLS_RAW_COLUMN_NAMES
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES


def test_callraw_dataclass_fields_match_calls_raw_spec_order() -> None:
    """CallRaw field order must remain aligned with calls_raw storage spec columns."""
    assert tuple(field.name for field in fields(CallRaw)) == CALLS_RAW_COLUMN_NAMES


def test_positionrow_dataclass_fields_match_position_rows_spec_order() -> None:
    """PositionRow field order must remain aligned with position_rows storage spec columns."""
    assert tuple(field.name for field in fields(PositionRow)) == POSITION_ROWS_COLUMN_NAMES
