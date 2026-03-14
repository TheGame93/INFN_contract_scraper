"""Split mutool PDF text into per-entry segments."""

from __future__ import annotations

import re

# Header keywords that start a new contract entry
_HEADER_RE = re.compile(
    r"^(?:CONTRATTO\s+DI\s+RICERCA|BORSA\s+DI\s+STUDIO|INCARICO\s+(?:DI\s+RICERCA|POST.?DOC)|"
    r"ASSEGNO\s+DI\s+RICERCA)",
    re.IGNORECASE | re.MULTILINE,
)


def _line_for_match(text: str, match: re.Match[str]) -> str:
    """Return full line containing match."""
    start = match.start()
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def _is_probable_header_line(line: str) -> bool:
    """Heuristic: segment headers usually start with an uppercase initial."""
    stripped = line.lstrip()
    return bool(stripped) and stripped[0].isupper()


def segment(text: str) -> list[str]:
    """Split mutool text output into per-entry segments. Returns list with at least one element."""
    if not text:
        return [""]

    # Normalize form-feed to newline so split logic works uniformly
    normalized = text.replace("\x0c", "\n")

    # Find all positions where a new contract header starts
    matches = list(_HEADER_RE.finditer(normalized))

    if len(matches) <= 1:
        # Single entry or no header found — return whole text as one segment
        return [text.strip()]

    # Guard against false splits on inline/lowercase mentions like "borsa di studio."
    filtered_matches = [
        m for m in matches if _is_probable_header_line(_line_for_match(normalized, m))
    ]
    split_points = filtered_matches if len(filtered_matches) >= 2 else matches

    if len(split_points) <= 1:
        return [text.strip()]

    segments = []
    for i, match in enumerate(split_points):
        start = match.start()
        end = split_points[i + 1].start() if i + 1 < len(split_points) else len(normalized)
        seg = normalized[start:end].strip()
        if seg:
            segments.append(seg)

    return segments if segments else [text.strip()]
