"""Tests for deterministic parser review-mode artifacts."""

from pathlib import Path

from infn_jobs.extract.parse.diagnostics.review_mode import build_review_report, render_review_report

FIXTURES = Path("tests/fixtures/pdf_text")


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_build_review_report_single_contract_contains_rule_ids() -> None:
    """Review report should include stable winner rule IDs and values."""
    report = build_review_report(
        text=_read("single_contract.txt"),
        detail_id="review-1",
        text_quality="digital",
        anno=2022,
    )

    assert report.detail_id == "review-1"
    assert len(report.segments) == 1
    segment = report.segments[0]
    assert segment.contract_type == "Contratto di ricerca"
    assert segment.winner_rule_ids["contract_type"] == "contract_identity.00.first_match.type"
    assert segment.winner_rule_ids["duration"] is not None
    assert "rule_executor" in report.diagnostics_rendered


def test_render_review_report_emits_deterministic_text_block() -> None:
    """Rendered review output should expose segment summary and diagnostics."""
    report = build_review_report(
        text=_read("single_contract.txt"),
        detail_id="review-2",
        text_quality="digital",
        anno=2022,
    )
    rendered = render_review_report(report)
    assert "detail_id=review-2" in rendered
    assert "segment_count=1" in rendered
    assert "segment[0]" in rendered
    assert "rules=" in rendered
    assert "diagnostics:" in rendered
