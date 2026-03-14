"""Fixture integrity guard for detail_id=4490 multiline parsing signals."""

from __future__ import annotations

from pathlib import Path

_FIXTURE = Path("tests/fixtures/pdf_text/canary/detail_4490.txt")


def _nonempty_lines(text: str) -> list[str]:
    """Return stripped non-empty lines preserving original order."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def test_detail_4490_fixture_keeps_required_subtype_and_income_phrases() -> None:
    """Canary fixture should retain phrases required by subtype/income regressions."""
    lines = _nonempty_lines(_FIXTURE.read_text(encoding="utf-8"))

    assert any("Fascia 1" in line for line in lines)
    assert any("L'importo annuo complessivo" in line and "27.819,00" in line for line in lines)
    assert any("oneri a carico dell’Istituto" in line for line in lines)
    assert any("compenso lordo annuo omnicomprensivo" in line for line in lines)
    assert any("22.500,00" in line for line in lines)


def test_detail_4490_fixture_keeps_split_line_gross_income_pattern() -> None:
    """Gross income label and amount must remain on adjacent lines for multiline tests."""
    lines = _nonempty_lines(_FIXTURE.read_text(encoding="utf-8"))

    label_index = next(
        index
        for index, line in enumerate(lines)
        if "compenso lordo annuo omnicomprensivo" in line and "pari ad €" in line
    )
    assert label_index + 1 < len(lines)
    assert lines[label_index + 1].startswith("22.500,00")


def test_detail_4490_fixture_keeps_institute_cost_context_adjacent() -> None:
    """Institute-cost amount line should stay adjacent to oneri-context line."""
    lines = _nonempty_lines(_FIXTURE.read_text(encoding="utf-8"))

    total_index = next(
        index
        for index, line in enumerate(lines)
        if "L'importo annuo complessivo" in line and "27.819,00" in line
    )
    assert total_index + 1 < len(lines)
    assert "oneri a carico dell’Istituto" in lines[total_index + 1]
