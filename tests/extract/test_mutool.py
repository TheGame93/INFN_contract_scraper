"""Tests for the mutool PDF text extractor."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from infn_jobs.domain.enums import TextQuality
from infn_jobs.extract.pdf.mutool import extract_text

DUMMY_PDF = Path("dummy.pdf")


def _completed(returncode: int, stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_extract_text_ok_returns_text_and_digital(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    stdout = "CONTRATTO DI RICERCA\nDurata: 12 mesi\nCompenso lordo annuo: € 28.000,00\n"
    with patch("subprocess.run", return_value=_completed(0, stdout)):
        text, quality = extract_text(pdf)
    assert text == stdout
    assert quality == TextQuality.DIGITAL


def test_extract_text_empty_output_returns_no_text(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    with patch("subprocess.run", return_value=_completed(0, "   \n")):
        _, quality = extract_text(pdf)
    assert quality == TextQuality.NO_TEXT


def test_extract_text_garbled_returns_ocr_degraded(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    stdout = "C0NTR4TT0 Dl R|C3RC4 @#$%^& !!!! |||"
    with patch("subprocess.run", return_value=_completed(0, stdout)):
        _, quality = extract_text(pdf)
    assert quality == TextQuality.OCR_DEGRADED


def test_extract_text_formfeed_signal_returns_ocr_clean(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    stdout = "\x0cDurata: 12 mesi\nCompenso lordo annuo: euro 28000\nSezione di Milano"
    with patch("subprocess.run", return_value=_completed(0, stdout)):
        _, quality = extract_text(pdf)
    assert quality == TextQuality.OCR_CLEAN


def test_extract_text_subprocess_failure_raises(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    with patch("subprocess.run", return_value=_completed(1, "")):
        with pytest.raises(RuntimeError):
            extract_text(pdf)


def test_extract_text_mutool_not_found_raises(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    with patch("subprocess.run", side_effect=FileNotFoundError("mutool not found")):
        with pytest.raises(RuntimeError):
            extract_text(pdf)
