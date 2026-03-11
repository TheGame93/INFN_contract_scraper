"""Projection spec for the position_rows_curated analytical view."""

from __future__ import annotations

from infn_jobs.store.spec.types import ViewColumnSpec, ViewSpec

POSITION_ROWS_CURATED_VIEW_SPEC = ViewSpec(
    name="position_rows_curated",
    columns=(
        ViewColumnSpec("detail_id", "pr.detail_id"),
        ViewColumnSpec("position_row_index", "pr.position_row_index"),
        ViewColumnSpec("source_tipo", "c.source_tipo"),
        ViewColumnSpec("listing_status", "c.listing_status"),
        ViewColumnSpec("numero", "c.numero"),
        ViewColumnSpec("anno", "c.anno"),
        ViewColumnSpec("numero_posti_html", "c.numero_posti_html"),
        ViewColumnSpec("data_bando", "c.data_bando"),
        ViewColumnSpec("data_scadenza", "c.data_scadenza"),
        ViewColumnSpec("first_seen_at", "c.first_seen_at"),
        ViewColumnSpec("last_synced_at", "c.last_synced_at"),
        ViewColumnSpec("pdf_fetch_status", "c.pdf_fetch_status"),
        ViewColumnSpec("detail_url", "c.detail_url"),
        ViewColumnSpec("pdf_url", "c.pdf_url"),
        ViewColumnSpec("pdf_cache_path", "c.pdf_cache_path"),
        ViewColumnSpec("call_title", "COALESCE(c.pdf_call_title, c.titolo)"),
        ViewColumnSpec("text_quality", "pr.text_quality"),
        ViewColumnSpec("contract_type", "pr.contract_type"),
        ViewColumnSpec("contract_type_raw", "pr.contract_type_raw"),
        ViewColumnSpec("contract_subtype", "pr.contract_subtype"),
        ViewColumnSpec("contract_subtype_raw", "pr.contract_subtype_raw"),
        ViewColumnSpec("duration_months", "pr.duration_months"),
        ViewColumnSpec("duration_raw", "pr.duration_raw"),
        ViewColumnSpec("section_structure_department", "pr.section_structure_department"),
        ViewColumnSpec("institute_cost_total_eur", "pr.institute_cost_total_eur"),
        ViewColumnSpec("institute_cost_yearly_eur", "pr.institute_cost_yearly_eur"),
        ViewColumnSpec("gross_income_total_eur", "pr.gross_income_total_eur"),
        ViewColumnSpec("gross_income_yearly_eur", "pr.gross_income_yearly_eur"),
        ViewColumnSpec("net_income_total_eur", "pr.net_income_total_eur"),
        ViewColumnSpec("net_income_yearly_eur", "pr.net_income_yearly_eur"),
        ViewColumnSpec("net_income_monthly_eur", "pr.net_income_monthly_eur"),
        ViewColumnSpec("contract_type_evidence", "pr.contract_type_evidence"),
        ViewColumnSpec("contract_subtype_evidence", "pr.contract_subtype_evidence"),
        ViewColumnSpec("duration_evidence", "pr.duration_evidence"),
        ViewColumnSpec("section_evidence", "pr.section_evidence"),
        ViewColumnSpec("institute_cost_evidence", "pr.institute_cost_evidence"),
        ViewColumnSpec("gross_income_evidence", "pr.gross_income_evidence"),
        ViewColumnSpec("net_income_evidence", "pr.net_income_evidence"),
        ViewColumnSpec("parse_confidence", "pr.parse_confidence"),
    ),
    from_clause="FROM position_rows pr\nJOIN calls_curated c ON pr.detail_id = c.detail_id",
)

POSITION_ROWS_CURATED_OUTPUT_COLUMNS = POSITION_ROWS_CURATED_VIEW_SPEC.column_names
