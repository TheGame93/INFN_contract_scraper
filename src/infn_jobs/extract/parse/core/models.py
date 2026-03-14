"""Typed models for parser orchestration inputs and outputs."""

from __future__ import annotations

from dataclasses import dataclass, field

from infn_jobs.domain.position import PositionRow


@dataclass(frozen=True)
class ParseRequest:
    """Input payload for one parser execution."""

    text: str
    detail_id: str
    text_quality: str
    anno: int | None


@dataclass
class ParseResult:
    """Output payload produced by one parser execution."""

    rows: list[PositionRow] = field(default_factory=list)
    pdf_call_title: str | None = None

