# detail_id=4447 Expected Parse Snapshot

This file is the agreed baseline used by Step 1 regression gates.

- **detail_id:** `4447`
- **source fixture:** `tests/fixtures/pdf_text/regression/detail_4447.txt`
- **extraction source:** `data/pdf_cache/4447.pdf` via `mutool draw -F txt`
- **captured on:** `2026-03-14`
- **status:** approved baseline for strict regression assertions

## Expected Outputs

- `rows_count`: `1`
- `pdf_call_title`: `Istituto Nazionale di Fisica Nucleare`
- `rows[0].contract_type`: `Incarico Post-Doc`
- `rows[0].contract_type_raw`: `INCARICO POST-DOC`
- `rows[0].duration_months`: `24`
- `rows[0].duration_raw`: `24 mesi`
- `rows[0].section_structure_department`: `Sezione di Firenze dell’INFN.`
- `rows[0].contract_subtype`: `NULL`
- Financial fields (`institute_cost_*`, `gross_income_*`, `net_income_*`): `NULL`
- `rows[0].parse_confidence`: `medium`
- `rows[0].text_quality`: `ocr_clean`
