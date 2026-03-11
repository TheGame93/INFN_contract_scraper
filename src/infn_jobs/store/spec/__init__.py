"""Store schema specifications for deterministic SQL generation."""

from infn_jobs.store.spec.calls_raw import (
    CALLS_CURATED_COLUMN_NAMES,
    CALLS_CURATED_SPEC,
    CALLS_RAW_COLUMN_NAMES,
    CALLS_RAW_SPEC,
)
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES, POSITION_ROWS_SPEC
from infn_jobs.store.spec.position_rows_curated import (
    POSITION_ROWS_CURATED_OUTPUT_COLUMNS,
    POSITION_ROWS_CURATED_VIEW_SPEC,
)
from infn_jobs.store.spec.types import ColumnSpec, TableSpec, ViewColumnSpec, ViewSpec

__all__ = [
    "CALLS_CURATED_COLUMN_NAMES",
    "CALLS_CURATED_SPEC",
    "CALLS_RAW_COLUMN_NAMES",
    "CALLS_RAW_SPEC",
    "ColumnSpec",
    "POSITION_ROWS_COLUMN_NAMES",
    "POSITION_ROWS_CURATED_OUTPUT_COLUMNS",
    "POSITION_ROWS_CURATED_VIEW_SPEC",
    "POSITION_ROWS_SPEC",
    "TableSpec",
    "ViewColumnSpec",
    "ViewSpec",
]
