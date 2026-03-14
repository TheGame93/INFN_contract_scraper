"""Run mutool to extract text from PDFs and classify text quality."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from infn_jobs.domain.enums import TextQuality
from infn_jobs.extract.pdf.text_quality import classify_text_quality

logger = logging.getLogger(__name__)


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
    quality = classify_text_quality(text)
    logger.debug("mutool %s: %s, %d chars", pdf_path.name, quality.value, len(text))
    return text, quality
