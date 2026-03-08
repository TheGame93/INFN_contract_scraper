"""Split mutool PDF text into per-entry segments."""

from __future__ import annotations

import re

# Header keywords that start a new contract entry
_HEADER_RE = re.compile(
    r"^(?:CONTRATTO\s+DI\s+RICERCA|BORSA\s+DI\s+STUDIO|INCARICO\s+(?:DI\s+RICERCA|POST.?DOC)|"
    r"ASSEGNO\s+DI\s+RICERCA)",
    re.IGNORECASE | re.MULTILINE,
)


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

    segments = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
        seg = normalized[start:end].strip()
        if seg:
            segments.append(seg)

    return segments if segments else [text.strip()]
