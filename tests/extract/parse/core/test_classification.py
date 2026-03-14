"""Tests for weighted segment classification."""

from infn_jobs.extract.parse.core.classification import classify_segment, classify_segments
from infn_jobs.extract.parse.core.models import SegmentSpan


def test_classify_segment_prefers_strong_header_match() -> None:
    """Weighted classification should detect the strongest contract-family match."""
    text = "INCARICO POST-DOC\nDettaglio selezione."
    result = classify_segment(text)
    assert result.contract_type == "Incarico Post-Doc"
    assert result.confidence > 0.0


def test_classify_segment_tie_break_is_deterministic() -> None:
    """Ties should resolve deterministically by canonical-name ordering."""
    text = "Contratto di ricerca\nIncarico di ricerca"
    result = classify_segment(text)
    assert result.contract_type == "Contratto di ricerca"


def test_classify_segments_preserves_input_order() -> None:
    """Batch classification should keep segment order stable."""
    spans = [
        SegmentSpan(text="BORSA DI STUDIO", source_line_start=1, source_line_end=1),
        SegmentSpan(text="ASSEGNO DI RICERCA", source_line_start=2, source_line_end=2),
    ]
    results = classify_segments(spans)
    assert [res.contract_type for res in results] == ["Borsa di studio", "Assegno di ricerca"]

