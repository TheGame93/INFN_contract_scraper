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


@dataclass(frozen=True)
class PreprocessResult:
    """Normalized text plus source-line mapping for traceability."""

    normalized_text: str
    source_line_map: tuple[int, ...]


@dataclass(frozen=True)
class SegmentSpan:
    """One segmented text chunk with source-line boundaries."""

    text: str
    source_line_start: int | None
    source_line_end: int | None


@dataclass(frozen=True)
class SegmentClassification:
    """Weighted contract-family classification for one segment."""

    contract_type: str | None
    confidence: float
    score_by_contract: tuple[tuple[str, int], ...]
