"""Policy helpers for PDF text-quality classification."""

from __future__ import annotations

from infn_jobs.domain.enums import TextQuality

OCR_SIGNALS = ("durata", "sezione", "compenso", "bando", "ricerca", "borsa")
GARBLED_RATIO_THRESHOLD = 0.30
MIN_READABLE_CHARS = 50


def classify_text_quality(text: str) -> TextQuality:
    """Classify mutool-extracted text into one deterministic quality bucket."""
    stripped = text.strip()
    if not stripped:
        return TextQuality.NO_TEXT

    non_word = sum(1 for char in stripped if not char.isalnum() and not char.isspace())
    total = len(stripped)
    if non_word / total > GARBLED_RATIO_THRESHOLD:
        return TextQuality.OCR_DEGRADED

    if len(stripped) < MIN_READABLE_CHARS:
        return TextQuality.NO_TEXT

    lower = stripped.lower()
    has_formfeed = "\x0c" in text
    has_italian_signal = any(word in lower for word in OCR_SIGNALS)
    if has_formfeed and has_italian_signal:
        return TextQuality.OCR_CLEAN

    return TextQuality.DIGITAL
