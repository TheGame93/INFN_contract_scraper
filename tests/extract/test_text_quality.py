"""Tests for text-quality classification policy."""

from infn_jobs.domain.enums import TextQuality
from infn_jobs.extract.pdf.text_quality import classify_text_quality


def test_classify_text_quality_no_text_for_blank_input():
    assert classify_text_quality("   \n") == TextQuality.NO_TEXT


def test_classify_text_quality_degraded_for_high_symbol_ratio():
    text = "C0NTR4TT0 Dl R|C3RC4 @#$%^& !!!! |||"
    assert classify_text_quality(text) == TextQuality.OCR_DEGRADED


def test_classify_text_quality_no_text_for_short_readable_text():
    text = "Contratto di ricerca durata 12 mesi"
    assert classify_text_quality(text) == TextQuality.NO_TEXT


def test_classify_text_quality_ocr_clean_for_formfeed_plus_italian_signals():
    text = "\x0cDurata contratto: 12 mesi\nCompenso lordo annuo: euro 28000\nSezione di Milano"
    assert classify_text_quality(text) == TextQuality.OCR_CLEAN


def test_classify_text_quality_digital_for_long_readable_text_without_formfeed():
    text = (
        "CONTRATTO DI RICERCA\n"
        "Durata: 12 mesi\n"
        "Compenso lordo annuo: euro 28000\n"
        "La selezione avviene per titoli ed esami."
    )
    assert classify_text_quality(text) == TextQuality.DIGITAL
