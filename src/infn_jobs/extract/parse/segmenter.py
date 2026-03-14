"""Split mutool PDF text into per-entry segments."""

from __future__ import annotations

from infn_jobs.extract.parse.core.preprocess import preprocess_text
from infn_jobs.extract.parse.core.segmentation import segment_preprocessed


def segment(text: str) -> list[str]:
    """Split mutool text output into per-entry segments. Returns list with at least one element."""
    if not text:
        return [""]

    spans = segment_preprocessed(preprocess_text(text))
    segments = [span.text for span in spans if span.text]
    return segments if segments else [text.strip()]
