"""Extract duration fields through the rule-driven duration adapter."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.duration import resolve_duration


def extract_duration(segment: str) -> tuple[int | None, str | None, str | None]:
    """Extract duration from a segment. Returns (duration_months, duration_raw, evidence)."""
    resolved = resolve_duration(segment_text=segment)
    return resolved.duration_months, resolved.duration_raw, resolved.evidence
