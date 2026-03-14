"""Weighted contract-family classification for parser segments."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.contracts.registry import list_profiles
from infn_jobs.extract.parse.core.models import SegmentClassification, SegmentSpan


def _score_contract(segment_text: str, aliases: tuple[str, ...]) -> int:
    """Return weighted score for aliases found in segment_text."""
    score = 0
    for alias in aliases:
        pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(segment_text):
            score += 2
            if match.start() == 0 or segment_text[match.start() - 1] == "\n":
                score += 2
            if match.group(0).isupper():
                score += 1
    return score


def classify_segment(segment_text: str) -> SegmentClassification:
    """Classify one segment into a contract family with deterministic tie-breaks."""
    scored: list[tuple[str, int]] = []
    for profile in list_profiles():
        scored.append(
            (
                profile.canonical_name,
                _score_contract(segment_text, profile.aliases),
            )
        )

    scored_sorted = sorted(scored, key=lambda item: (-item[1], item[0]))
    top_name, top_score = scored_sorted[0]
    total = sum(score for _, score in scored_sorted)

    if top_score <= 0 or total <= 0:
        return SegmentClassification(
            contract_type=None,
            confidence=0.0,
            score_by_contract=tuple(sorted(scored, key=lambda item: item[0])),
        )

    confidence = top_score / total
    return SegmentClassification(
        contract_type=top_name,
        confidence=confidence,
        score_by_contract=tuple(sorted(scored, key=lambda item: item[0])),
    )


def classify_segments(spans: list[SegmentSpan]) -> list[SegmentClassification]:
    """Classify all segment spans in order."""
    return [classify_segment(span.text) for span in spans]

