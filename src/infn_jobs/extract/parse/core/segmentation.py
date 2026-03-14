"""Deterministic segmentation over preprocessed parser text."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.core.models import PreprocessResult, SegmentSpan

_HEADER_RE = re.compile(
    r"^(?:CONTRATTO\s+DI\s+RICERCA|BORSA\s+DI\s+STUDIO|INCARICO\s+(?:DI\s+RICERCA|POST.?DOC)|"
    r"ASSEGNO\s+DI\s+RICERCA)",
    re.IGNORECASE,
)


def _is_header_start(line: str) -> bool:
    """Return True when line begins with a known contract header."""
    return bool(_HEADER_RE.match(line.strip()))


def _is_uppercase_header_line(line: str) -> bool:
    """Return True when a candidate header starts with an uppercase letter."""
    stripped = line.lstrip()
    return bool(stripped) and stripped[0].isupper()


def _single_span(preprocessed: PreprocessResult) -> list[SegmentSpan]:
    """Return one span covering the full preprocessed text payload."""
    text = preprocessed.normalized_text.strip()
    if not text:
        return []
    line_count = len(preprocessed.normalized_text.splitlines())
    start_line = preprocessed.source_line_map[0] if preprocessed.source_line_map else None
    end_line = (
        preprocessed.source_line_map[line_count - 1]
        if preprocessed.source_line_map and line_count > 0
        else start_line
    )
    return [SegmentSpan(text=text, source_line_start=start_line, source_line_end=end_line)]


def segment_preprocessed(preprocessed: PreprocessResult) -> list[SegmentSpan]:
    """Split preprocessed text into deterministic segment spans."""
    if not preprocessed.normalized_text:
        return []

    lines = preprocessed.normalized_text.splitlines()
    if not lines:
        return _single_span(preprocessed)

    raw_starts = [idx for idx, line in enumerate(lines) if _is_header_start(line)]
    if len(raw_starts) <= 1:
        return _single_span(preprocessed)

    filtered_starts = [idx for idx in raw_starts if _is_uppercase_header_line(lines[idx])]
    split_starts = filtered_starts if len(filtered_starts) >= 2 else raw_starts
    if len(split_starts) <= 1:
        return _single_span(preprocessed)

    spans: list[SegmentSpan] = []
    for i, start_idx in enumerate(split_starts):
        end_idx = split_starts[i + 1] if i + 1 < len(split_starts) else len(lines)
        text = "\n".join(lines[start_idx:end_idx]).strip()
        if not text:
            continue
        source_line_start = preprocessed.source_line_map[start_idx]
        source_line_end = preprocessed.source_line_map[end_idx - 1]
        spans.append(
            SegmentSpan(
                text=text,
                source_line_start=source_line_start,
                source_line_end=source_line_end,
            )
        )

    return spans if spans else _single_span(preprocessed)

