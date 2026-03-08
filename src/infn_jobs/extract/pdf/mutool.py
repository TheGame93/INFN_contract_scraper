"""Run mutool to extract text from PDFs and classify text quality."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from infn_jobs.domain.enums import TextQuality

logger = logging.getLogger(__name__)

# Italian words that indicate readable (possibly OCR'd) text
_OCR_SIGNALS = ("durata", "sezione", "compenso", "bando", "ricerca", "borsa")


def _classify(text: str) -> TextQuality:
    """Classify text quality based on content heuristics."""
    stripped = text.strip()
    if not stripped:
        return TextQuality.NO_TEXT

    # Check garbled ratio before length gate — garbled short text is still OCR_DEGRADED
    non_word = sum(1 for c in stripped if not c.isalnum() and not c.isspace())
    total = len(stripped)
    if non_word / total > 0.30:
        return TextQuality.OCR_DEGRADED

    if len(stripped) < 50:
        return TextQuality.NO_TEXT

    lower = stripped.lower()
    has_formfeed = "\x0c" in text
    has_italian = any(word in lower for word in _OCR_SIGNALS)
    if has_formfeed and has_italian:
        return TextQuality.OCR_CLEAN

    return TextQuality.DIGITAL


def extract_text(pdf_path: Path) -> tuple[str, TextQuality]:
    """Run mutool draw -F txt on pdf_path. Returns (text, text_quality)."""
    try:
        result = subprocess.run(
            ["mutool", "draw", "-F", "txt", str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"mutool not found: {exc}") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"mutool failed (rc={result.returncode}): {result.stderr.strip()}"
        )

    text = result.stdout
    quality = _classify(text)
    logger.debug("mutool %s: %s, %d chars", pdf_path.name, quality.value, len(text))
    return text, quality
