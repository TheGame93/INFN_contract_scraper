"""Shared segment execution internals used by runtime and review parser flows."""

from __future__ import annotations

from dataclasses import dataclass

from infn_jobs.extract.parse.core.classification import classify_segments
from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed
from infn_jobs.extract.parse.fields.metadata import extract_pdf_call_title
from infn_jobs.extract.parse.rules.contract_identity import (
    ContractIdentityResolution,
    resolve_contract_identity,
)
from infn_jobs.extract.parse.rules.duration import DurationResolution, resolve_duration
from infn_jobs.extract.parse.rules.income import IncomeResolution, resolve_income
from infn_jobs.extract.parse.rules.section import SectionResolution, resolve_section


@dataclass(frozen=True)
class _ExecutedSegment:
    """Segment-level parse outcomes and trace metadata for one pipeline pass."""

    segment_index: int
    segment_text: str
    source_line_start: int | None
    source_line_end: int | None
    predicted_contract_type: str | None
    predicted_confidence: float
    identity: ContractIdentityResolution
    duration: DurationResolution
    income: IncomeResolution
    section: SectionResolution


@dataclass(frozen=True)
class _ExecutionBundle:
    """Shared parse execution outputs for runtime and review wrappers."""

    pdf_call_title: str | None
    segments: tuple[_ExecutedSegment, ...]


def _execute_segments(*, text: str, detail_id: str, anno: int | None) -> _ExecutionBundle:
    """Run deterministic parse phases and return segment-level execution artifacts."""
    pdf_call_title = extract_pdf_call_title(text)
    spans = segment_preprocessed(preprocess_text(text))
    if not spans:
        return _ExecutionBundle(pdf_call_title=pdf_call_title, segments=())

    classifications = classify_segments(spans)
    segments: list[_ExecutedSegment] = []
    for index, span in enumerate(spans):
        segment_text = span.text
        identity = resolve_contract_identity(
            segment_text=segment_text,
            anno=anno,
            predicted_contract_type=classifications[index].contract_type,
            detail_id=detail_id,
        )
        duration = resolve_duration(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )
        income = resolve_income(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )
        section = resolve_section(
            segment_text=segment_text,
            detail_id=detail_id,
            anno=anno,
            contract_type=identity.contract_type,
        )
        segments.append(
            _ExecutedSegment(
                segment_index=index,
                segment_text=segment_text,
                source_line_start=span.source_line_start,
                source_line_end=span.source_line_end,
                predicted_contract_type=classifications[index].contract_type,
                predicted_confidence=classifications[index].confidence,
                identity=identity,
                duration=duration,
                income=income,
                section=section,
            )
        )

    return _ExecutionBundle(pdf_call_title=pdf_call_title, segments=tuple(segments))
