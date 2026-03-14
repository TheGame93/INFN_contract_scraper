"""Tests for scripts/review_parse_case.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from infn_jobs.domain.enums import TextQuality


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_parse_case_prints_report_with_monkeypatched_extract(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    """Review script should print deterministic report for one requested detail_id."""
    module = _load_module(Path("scripts/review_parse_case.py"))
    fixture_text = Path("tests/fixtures/pdf_text/single_contract.txt").read_text(encoding="utf-8")
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(module, "extract_text", lambda _path: (fixture_text, TextQuality.DIGITAL))

    exit_code = module.main(
        [
            "--detail-id",
            "script-1",
            "--pdf-path",
            str(pdf_path),
            "--anno",
            "2022",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "detail_id=script-1" in output
    assert "segment_count=1" in output
