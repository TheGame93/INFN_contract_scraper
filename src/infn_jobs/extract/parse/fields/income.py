"""Extract EUR income and cost fields via the rule-driven income adapter."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.income import resolve_income


def extract_income(segment: str) -> dict:
    """Extract all 7 EUR income/cost fields and 3 evidence fields from a segment."""
    resolved = resolve_income(segment_text=segment)
    return {
        "institute_cost_total_eur": resolved.values["institute_cost_total_eur"],
        "institute_cost_yearly_eur": resolved.values["institute_cost_yearly_eur"],
        "gross_income_total_eur": resolved.values["gross_income_total_eur"],
        "gross_income_yearly_eur": resolved.values["gross_income_yearly_eur"],
        "net_income_total_eur": resolved.values["net_income_total_eur"],
        "net_income_yearly_eur": resolved.values["net_income_yearly_eur"],
        "net_income_monthly_eur": resolved.values["net_income_monthly_eur"],
        "institute_cost_evidence": resolved.values["institute_cost_evidence"],
        "gross_income_evidence": resolved.values["gross_income_evidence"],
        "net_income_evidence": resolved.values["net_income_evidence"],
    }
