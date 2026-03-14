"""Rule specification table for income field adapters."""

from __future__ import annotations

from typing import Any

from infn_jobs.extract.parse.rules import income_helpers

INCOME_FIELD_RULE_SPECS: dict[str, tuple[dict[str, Any], ...]] = {
    "institute_cost_total_eur": (
        {
            "rule_id": "income.institute.total.primary",
            "tier": "primary",
            "label_re": income_helpers.INSTITUTE_RE,
            "require_total": True,
        },
        {
            "rule_id": "income.institute.total.fallback_unqualified",
            "tier": "fallback",
            "label_re": income_helpers.INSTITUTE_RE,
            "require_no_qualifier": True,
        },
    ),
    "institute_cost_yearly_eur": (
        {
            "rule_id": "income.institute.yearly.primary",
            "tier": "primary",
            "label_re": income_helpers.INSTITUTE_RE,
            "require_yearly": True,
        },
    ),
    "gross_income_total_eur": (
        {
            "rule_id": "income.gross.total.primary",
            "tier": "primary",
            "label_re": income_helpers.GROSS_RE,
            "require_total": True,
        },
    ),
    "gross_income_yearly_eur": (
        {
            "rule_id": "income.gross.yearly.primary",
            "tier": "primary",
            "label_re": income_helpers.GROSS_RE,
            "require_yearly": True,
        },
        {
            "rule_id": "income.gross.yearly.fallback_unqualified",
            "tier": "fallback",
            "label_re": income_helpers.GROSS_RE,
            "require_no_qualifier": True,
        },
    ),
    "net_income_total_eur": (
        {
            "rule_id": "income.net.total.primary",
            "tier": "primary",
            "label_re": income_helpers.NET_RE,
            "require_total": True,
        },
    ),
    "net_income_yearly_eur": (
        {
            "rule_id": "income.net.yearly.primary",
            "tier": "primary",
            "label_re": income_helpers.NET_RE,
            "require_yearly": True,
        },
        {
            "rule_id": "income.net.yearly.fallback_unqualified",
            "tier": "fallback",
            "label_re": income_helpers.NET_RE,
            "require_no_qualifier": True,
        },
    ),
    "net_income_monthly_eur": (
        {
            "rule_id": "income.net.monthly.primary",
            "tier": "primary",
            "label_re": income_helpers.NET_RE,
            "require_monthly": True,
        },
    ),
}
