"""Extract call-level and segment-level metadata from PDF text."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.section import resolve_section


def extract_pdf_call_title(text: str) -> str | None:
    """Extract call-level title from full PDF text (before segmentation)."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def extract_section_department(segment: str) -> tuple[str | None, str | None]:
    """Extract section/structure/department from one segment. Returns (value, evidence)."""
    resolved = resolve_section(segment_text=segment)
    return resolved.value, resolved.evidence
