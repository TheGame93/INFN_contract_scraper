"""Column and table specs for position_rows."""

from __future__ import annotations

from infn_jobs.store.spec.types import ColumnSpec, TableSpec

POSITION_ROWS_SPEC = TableSpec(
    name="position_rows",
    columns=(
        ColumnSpec("detail_id", "TEXT"),
        ColumnSpec("position_row_index", "INTEGER"),
        ColumnSpec("text_quality", "TEXT"),
        ColumnSpec("contract_type", "TEXT"),
        ColumnSpec("contract_type_raw", "TEXT"),
        ColumnSpec("contract_subtype", "TEXT"),
        ColumnSpec("contract_subtype_raw", "TEXT"),
        ColumnSpec("duration_months", "INTEGER"),
        ColumnSpec("duration_raw", "TEXT"),
        ColumnSpec("section_structure_department", "TEXT"),
        ColumnSpec("institute_cost_total_eur", "REAL"),
        ColumnSpec("institute_cost_yearly_eur", "REAL"),
        ColumnSpec("gross_income_total_eur", "REAL"),
        ColumnSpec("gross_income_yearly_eur", "REAL"),
        ColumnSpec("net_income_total_eur", "REAL"),
        ColumnSpec("net_income_yearly_eur", "REAL"),
        ColumnSpec("net_income_monthly_eur", "REAL"),
        ColumnSpec("contract_type_evidence", "TEXT"),
        ColumnSpec("contract_subtype_evidence", "TEXT"),
        ColumnSpec("duration_evidence", "TEXT"),
        ColumnSpec("section_evidence", "TEXT"),
        ColumnSpec("institute_cost_evidence", "TEXT"),
        ColumnSpec("gross_income_evidence", "TEXT"),
        ColumnSpec("net_income_evidence", "TEXT"),
        ColumnSpec("parse_confidence", "TEXT"),
    ),
    constraints=(
        "PRIMARY KEY (detail_id, position_row_index)",
        "FOREIGN KEY (detail_id) REFERENCES calls_raw(detail_id)",
    ),
)

POSITION_ROWS_COLUMN_NAMES = POSITION_ROWS_SPEC.column_names
