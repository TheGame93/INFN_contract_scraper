"""Deterministic SQL fragment helpers for store specs."""

from __future__ import annotations

from infn_jobs.store.spec.types import ColumnSpec, TableSpec, ViewSpec


def comma_separated(items: tuple[str, ...]) -> str:
    """Join items with a comma+space separator preserving order."""
    return ", ".join(items)


def named_placeholders(column_names: tuple[str, ...]) -> str:
    """Return SQLite named placeholders for column_names preserving order."""
    return ", ".join(f":{name}" for name in column_names)


def excluded_assignments(column_names: tuple[str, ...], indent: str = "            ") -> str:
    """Return ON CONFLICT assignment lines using excluded.<column> values."""
    return ",\n".join(f"{indent}{name} = excluded.{name}" for name in column_names)


def render_column_definition(column: ColumnSpec) -> str:
    """Render one column definition for CREATE TABLE statements."""
    return f"{column.name} {column.sql_type}"


def render_table_body(spec: TableSpec, indent: str = "    ") -> str:
    """Render CREATE TABLE body lines for columns and constraints."""
    lines = [f"{indent}{render_column_definition(column)}" for column in spec.columns]
    lines.extend(f"{indent}{constraint}" for constraint in spec.constraints)
    return ",\n".join(lines)


def render_view_select_list(spec: ViewSpec, indent: str = "    ") -> str:
    """Render SELECT projection lines with explicit aliases."""
    return ",\n".join(f"{indent}{column.expression} AS {column.name}" for column in spec.columns)
