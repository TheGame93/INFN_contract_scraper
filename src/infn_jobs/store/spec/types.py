"""Data types for table and view storage specifications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    """Describe one table column in storage specs."""

    name: str
    sql_type: str


@dataclass(frozen=True)
class TableSpec:
    """Describe one SQLite table in storage specs."""

    name: str
    columns: tuple[ColumnSpec, ...]
    constraints: tuple[str, ...] = ()

    @property
    def column_names(self) -> tuple[str, ...]:
        """Return ordered column names for this table."""
        return tuple(column.name for column in self.columns)


@dataclass(frozen=True)
class ViewColumnSpec:
    """Describe one output column in a SQLite view."""

    name: str
    expression: str


@dataclass(frozen=True)
class ViewSpec:
    """Describe one SQLite view projection in storage specs."""

    name: str
    columns: tuple[ViewColumnSpec, ...]
    from_clause: str

    @property
    def column_names(self) -> tuple[str, ...]:
        """Return ordered output column names for this view."""
        return tuple(column.name for column in self.columns)
