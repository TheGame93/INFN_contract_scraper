# Review/Runtime Parity Baseline

This document captures the Step 1 investigation baseline for `M01`.
It records parity evidence between:

- runtime path: `run_parse_pipeline(ParseRequest(...))`
- review path: `build_review_report(...)`

## Command used

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from infn_jobs.extract.parse.core.models import ParseRequest
from infn_jobs.extract.parse.core.orchestrator import run_parse_pipeline
from infn_jobs.extract.parse.diagnostics.review_mode import build_review_report

cases = [
    ("single_contract.txt", "digital", 2022),
    ("ocr_clean.txt", "ocr_clean", 2022),
    ("canary/detail_4358.txt", "ocr_clean", 2025),
]
root = Path("tests/fixtures/pdf_text")
for rel, quality, anno in cases:
    text = (root / rel).read_text(encoding="utf-8")
    detail_id = rel.replace('/', '-').replace('.txt','')
    runtime = run_parse_pipeline(ParseRequest(text=text, detail_id=detail_id, text_quality=quality, anno=anno))
    review = build_review_report(text=text, detail_id=detail_id, text_quality=quality, anno=anno)
    runtime_view = [
        {
            "contract_type": r.contract_type,
            "contract_subtype": r.contract_subtype,
            "duration_months": r.duration_months,
            "section": r.section_structure_department,
            "gross_income_yearly_eur": r.gross_income_yearly_eur,
        }
        for r in runtime.rows
    ]
    review_view = [
        {
            "contract_type": s.contract_type,
            "contract_subtype": s.contract_subtype,
            "duration_months": s.duration_months,
            "section": s.section_structure_department,
            "gross_income_yearly_eur": s.gross_income_yearly_eur,
        }
        for s in review.segments
    ]
    print(rel)
    print("  title_equal", runtime.pdf_call_title == review.pdf_call_title)
    print("  rows", len(runtime.rows), "segments", len(review.segments))
    print("  rows_equal", runtime_view == review_view)
    print("  winners_present", all(bool(s.winner_rule_ids.get('contract_type')) for s in review.segments))
PY
```

## Baseline results (2026-03-14)

| Fixture | `pdf_call_title` parity | row/segment parity | shared field parity | contract-type winner rule present |
|---|---|---|---|---|
| `single_contract.txt` | yes | `1 == 1` | yes | yes |
| `ocr_clean.txt` | yes | `1 == 1` | yes | yes |
| `canary/detail_4358.txt` | yes | `1 == 1` | yes | yes |

## Step 2 acceptance criteria

- Runtime and review mode must continue to match on Step 1 parity tests for the shared output projection.
- Any intentional divergence must be documented here before merging and accompanied by updated tests.
