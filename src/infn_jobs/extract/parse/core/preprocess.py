"""Text preprocessing with source-line traceability."""

from __future__ import annotations

from infn_jobs.extract.parse.core.models import PreprocessResult


def preprocess_text(text: str) -> PreprocessResult:
    """Normalize text while keeping a mapping to original line numbers."""
    if not text:
        return PreprocessResult(normalized_text="", source_line_map=())

    normalized_endings = text.replace("\r\n", "\n").replace("\r", "\n")
    processed_lines: list[str] = []
    source_line_map: list[int] = []

    source_lines = normalized_endings.split("\n")
    if source_lines and source_lines[-1] == "":
        source_lines = source_lines[:-1]

    for source_index, raw_line in enumerate(source_lines, start=1):
        # Form-feed boundaries are represented as synthetic new lines to keep segmentation stable.
        fragments = raw_line.split("\x0c")
        for fragment in fragments:
            processed_lines.append(fragment.rstrip())
            source_line_map.append(source_index)

    return PreprocessResult(
        normalized_text="\n".join(processed_lines),
        source_line_map=tuple(source_line_map),
    )
