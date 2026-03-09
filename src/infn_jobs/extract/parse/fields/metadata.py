"""Extract call-level and segment-level metadata from PDF text."""

from __future__ import annotations

import re

_SECTION_RE = re.compile(
    r"(Sezi?one\s+di\s+\S+(?:\s+\S+){0,3}|Sede\s+di\s+\S+(?:\s+\S+){0,3}|"
    r"Struttura\s+di\s+\S+(?:\s+\S+){0,3})",
    re.IGNORECASE,
)


def extract_pdf_call_title(text: str) -> str | None:
    """Extract call-level title from full PDF text (before segmentation)."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def extract_section_department(segment: str) -> tuple[str | None, str | None]:
    """Extract section/structure/department from one segment. Returns (value, evidence)."""
    for line in segment.splitlines():
        m = _SECTION_RE.search(line)
        if m:
            return m.group(1).strip(), line.strip()
    return None, None
