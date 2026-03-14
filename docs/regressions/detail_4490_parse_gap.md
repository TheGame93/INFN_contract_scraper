# detail_id=4490 Parse Gap Baseline

This document locks the pre-refactor parser baseline for `detail_id=4490`.
It is an investigation artifact for Step 1 of `docs/plan_codex_parsefixing.md`.

## Commands used

```bash
PYTHONPATH=src python3 scripts/review_parse_case.py --detail-id 4490 --pdf-path data/pdf_cache/4490.pdf --anno 2026
rg -n "Fascia 1|27\.819,00|22\.500,00|oneri a carico" tests/fixtures/pdf_text/canary/detail_4490.txt
```

## Current parser baseline (before fixes)

- `text_quality=ocr_clean`
- `predicted_contract_type=Incarico di ricerca`
- `contract_type=Incarico di ricerca`
- `contract_subtype` winner: `-` (no value)
- `institute_cost_total_eur` winner: `-` (no value)
- `gross_income_yearly_eur` winner: `-` (no value)

Relevant diagnostic rejections from `review_parse_case.py`:

- `rule_executor|rejected|contract_subtype|contract_identity.incarico-di-ricerca.subtype|no_value|-`
- `rule_executor|rejected|institute_cost_total_eur|income.institute.total.primary|no_value|-`
- `rule_executor|rejected|gross_income_yearly_eur|income.gross.yearly.primary|no_value|-`

## Ground-truth evidence in fixture text

- Subtype evidence: `detail_4490.txt:84` contains `rinnovabile, di Fascia 1, da fruire presso la Sezione di Bari dell’INFN.`
- Institute cost evidence:
  - `detail_4490.txt:132` contains `L'importo annuo complessivo ... € 27.819,00`
  - `detail_4490.txt:133` contains `comprensivo di oneri a carico dell’Istituto.`
- Gross yearly evidence:
  - `detail_4490.txt:134` contains `compenso lordo annuo omnicomprensivo pari ad €`
  - `detail_4490.txt:135` contains `22.500,00 ...`

## Gap summary

| Field | Current parser output | Ground-truth target |
|---|---|---|
| `contract_subtype` | `NULL` | `Fascia 1` |
| `institute_cost_total_eur` | `NULL` | `27.819,00` |
| `gross_income_yearly_eur` | `NULL` | `22.500,00` |

This baseline is intentionally frozen so Step 2-5 changes can be measured and validated against an explicit pre-change state.
