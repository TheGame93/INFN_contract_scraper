"""Tests for store/spec definitions and SQL helper determinism."""

from infn_jobs.store.spec.calls_raw import (
    CALLS_CURATED_COLUMN_NAMES,
    CALLS_RAW_COLUMN_NAMES,
    CALLS_RAW_SPEC,
)
from infn_jobs.store.spec.position_rows import POSITION_ROWS_COLUMN_NAMES
from infn_jobs.store.spec.position_rows_curated import POSITION_ROWS_CURATED_OUTPUT_COLUMNS
from infn_jobs.store.spec.sql_parts import (
    comma_separated,
    excluded_assignments,
    named_placeholders,
    render_table_body,
    render_view_select_list,
)
from infn_jobs.store.spec.types import ViewColumnSpec, ViewSpec


def test_calls_raw_columns_match_current_schema_order() -> None:
    """calls_raw ordered column names must match the existing schema contract."""
    assert CALLS_RAW_COLUMN_NAMES == (
        "detail_id",
        "source_tipo",
        "listing_status",
        "numero",
        "anno",
        "titolo",
        "pdf_call_title",
        "numero_posti_html",
        "data_bando",
        "data_scadenza",
        "detail_url",
        "pdf_url",
        "pdf_cache_path",
        "pdf_fetch_status",
        "first_seen_at",
        "last_synced_at",
    )


def test_calls_curated_columns_match_calls_raw_exactly() -> None:
    """calls_curated must reuse the exact calls_raw column sequence."""
    assert CALLS_CURATED_COLUMN_NAMES == CALLS_RAW_COLUMN_NAMES


def test_position_rows_columns_match_current_schema_order() -> None:
    """position_rows ordered column names must match the existing schema contract."""
    assert POSITION_ROWS_COLUMN_NAMES == (
        "detail_id",
        "position_row_index",
        "text_quality",
        "contract_type",
        "contract_type_raw",
        "contract_subtype",
        "contract_subtype_raw",
        "duration_months",
        "duration_raw",
        "section_structure_department",
        "institute_cost_total_eur",
        "institute_cost_yearly_eur",
        "gross_income_total_eur",
        "gross_income_yearly_eur",
        "net_income_total_eur",
        "net_income_yearly_eur",
        "net_income_monthly_eur",
        "contract_type_evidence",
        "contract_subtype_evidence",
        "duration_evidence",
        "section_evidence",
        "institute_cost_evidence",
        "gross_income_evidence",
        "net_income_evidence",
        "parse_confidence",
    )


def test_position_rows_curated_columns_match_current_view_order() -> None:
    """position_rows_curated output names must match the existing view contract."""
    assert POSITION_ROWS_CURATED_OUTPUT_COLUMNS == (
        "detail_id",
        "position_row_index",
        "source_tipo",
        "listing_status",
        "numero",
        "anno",
        "numero_posti_html",
        "data_bando",
        "data_scadenza",
        "first_seen_at",
        "last_synced_at",
        "pdf_fetch_status",
        "detail_url",
        "pdf_url",
        "pdf_cache_path",
        "call_title",
        "text_quality",
        "contract_type",
        "contract_type_raw",
        "contract_subtype",
        "contract_subtype_raw",
        "duration_months",
        "duration_raw",
        "section_structure_department",
        "institute_cost_total_eur",
        "institute_cost_yearly_eur",
        "gross_income_total_eur",
        "gross_income_yearly_eur",
        "net_income_total_eur",
        "net_income_yearly_eur",
        "net_income_monthly_eur",
        "contract_type_evidence",
        "contract_subtype_evidence",
        "duration_evidence",
        "section_evidence",
        "institute_cost_evidence",
        "gross_income_evidence",
        "net_income_evidence",
        "parse_confidence",
    )


def test_all_specs_have_unique_column_names() -> None:
    """All table/view specs must avoid duplicate output names."""
    for names in (
        CALLS_RAW_COLUMN_NAMES,
        CALLS_CURATED_COLUMN_NAMES,
        POSITION_ROWS_COLUMN_NAMES,
        POSITION_ROWS_CURATED_OUTPUT_COLUMNS,
    ):
        assert len(names) == len(set(names))


def test_comma_separated_preserves_order() -> None:
    """comma_separated must preserve tuple order deterministically."""
    assert comma_separated(("a", "b", "c")) == "a, b, c"


def test_named_placeholders_preserve_order() -> None:
    """named_placeholders must preserve tuple order deterministically."""
    assert named_placeholders(("detail_id", "source_tipo")) == ":detail_id, :source_tipo"


def test_excluded_assignments_preserve_order() -> None:
    """excluded_assignments must preserve tuple order deterministically."""
    assert excluded_assignments(("source_tipo", "listing_status")) == (
        "            source_tipo = excluded.source_tipo,\n"
        "            listing_status = excluded.listing_status"
    )


def test_render_table_body_includes_constraints_last() -> None:
    """render_table_body must render columns first and table constraints last."""
    body = render_table_body(CALLS_RAW_SPEC)
    lines = [line.strip() for line in body.splitlines()]
    assert lines[0] == "detail_id TEXT,"
    assert lines[-1] == "PRIMARY KEY (detail_id)"


def test_render_view_select_list_always_aliases_columns() -> None:
    """render_view_select_list must emit explicit aliases for each output column."""
    view_spec = ViewSpec(
        name="sample_view",
        columns=(
            ViewColumnSpec("first", "t.a"),
            ViewColumnSpec("second", "COALESCE(t.b, t.c)"),
        ),
        from_clause="FROM sample t",
    )
    assert render_view_select_list(view_spec) == (
        "    t.a AS first,\n"
        "    COALESCE(t.b, t.c) AS second"
    )
