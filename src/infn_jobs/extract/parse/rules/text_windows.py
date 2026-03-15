"""Shared adjacent-line text window helpers for deterministic rule matching."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextWindow:
    """One deterministic text window and its evidence snippet."""

    text: str
    evidence: str


def iter_nonempty_lines(segment_text: str) -> tuple[str, ...]:
    """Return normalized non-empty lines preserving source order."""
    lines: list[str] = []
    for raw_line in segment_text.splitlines():
        # Collapse internal spacing so wrapped tokens are matched consistently.
        normalized = re.sub(r"\s+", " ", raw_line.strip())
        if normalized:
            lines.append(normalized)
    return tuple(lines)


def iter_adjacent_line_windows(segment_text: str, max_lines: int = 2) -> tuple[TextWindow, ...]:
    """Return deterministic adjacent-line windows from non-empty segment lines."""
    if max_lines < 1:
        raise ValueError("max_lines must be >= 1")

    lines = iter_nonempty_lines(segment_text)
    windows: list[TextWindow] = []
    for start in range(len(lines)):
        for size in range(1, max_lines + 1):
            end = start + size
            if end > len(lines):
                break
            text = " ".join(lines[start:end])
            windows.append(TextWindow(text=text, evidence=text))
    return tuple(windows)
