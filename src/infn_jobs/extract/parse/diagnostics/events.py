"""Diagnostic event model for parser tracing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParseEvent:
    """Represent one parser diagnostic event."""

    stage: str
    message: str
    detail_id: str | None = None

