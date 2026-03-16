You are auditing canary contracts by updating ONLY the markdown tables in:

docs/audit_canariesmismatch.md

Goal:
Update each canary table so it compares:
1) `extracted from code` (from `data/infn_jobs.db`)
2) `extracted from CODEX` (your manual extraction from canary PDF in `data/pdf_cache`)
3) `comparison` using exactly: `✅`, `❌`, `⚪`
Legend rule: `⚪` only when CODEX value is `NOT_REVIEWED`.

Canary scope (fixed list for this audit run):
- `4507`, `4476`, `4490`, `4493`, `4484`, `4456`, `4358`, `4223`, `4302`, `4441`, `4458`
- Audit ONLY these detail_ids, in this order.

Hard constraints:
- Do NOT change any text outside markdown tables (headings, legend, prose, spacing outside tables must stay exactly as-is).
- Keep table headers unchanged: `field name | extracted from code | extracted from CODEX | comparison`.
- In each table, row set in first column (`field name`) must match current DB schema for that table:
  - add missing fields
  - remove obsolete fields
  - keep schema order (PRAGMA order).
- This document currently audits `position_rows` for `position_row_index = 0` per canary detail_id section.
- Use backticks around field names and values, as in existing file.
- Before updating canary tables, refresh the `Field provenance map` from current code paths and update it in BOTH:
  - `docs/plan_auditcanaries.md` (this file, section `Field provenance map`)
  - `docs/audit_canariesmismatch.md` (section `## Field Provenance Map (position_rows)`)
- The two provenance maps must stay logically aligned with each other and with current code.
- If a field is added/removed/renamed in schema, update provenance entries accordingly in both files.
- Only audit PDF-scrapable fields with manual CODEX extraction from PDF text.
- For non-PDF-scrapable fields, force `extracted from CODEX = NOT_REVIEWED` and `comparison = ⚪`.

Data source rules:
- `extracted from code`: read from SQLite `data/infn_jobs.db`, table `position_rows`, filter by section `detail_id` and `position_row_index = 0`.
- `extracted from CODEX`: manually extract from the matching canary PDF in `data/pdf_cache` for that `detail_id`.
- If a CODEX value cannot be confidently evaluated from PDF, set `NOT_REVIEWED`.
- Represent SQL null as `NULL`.

Field provenance map (`position_rows`):
- `detail_id`: WEB/detail metadata key (`calls_raw.detail_id`), not extracted from PDF text.
- `position_row_index`: derived from PDF segment order (`segment_index`), not directly from web/PDF labels.
- `text_quality`: derived from PDF text extraction quality classifier (`extract_text` + `classify_text_quality`).
- `contract_type`, `contract_type_raw`, `contract_type_evidence`: PDF text rules.
- `contract_subtype_raw`, `contract_subtype_evidence`: PDF text rules.
- `contract_subtype`: derived from `contract_subtype_raw` + normalization; can depend on `anno` context (WEB field `calls_raw.anno`) for era-gated mappings.
- `duration_months`, `duration_raw`, `duration_evidence`: PDF text rules.
- `section_structure_department`, `section_evidence`: PDF text rules.
- `institute_cost_total_eur`, `institute_cost_yearly_eur`, `gross_income_total_eur`, `gross_income_yearly_eur`, `net_income_total_eur`, `net_income_yearly_eur`, `net_income_monthly_eur`: PDF text rules.
- `institute_cost_evidence`, `gross_income_evidence`, `net_income_evidence`: PDF text rule evidence.
- `parse_confidence`: computed from extracted row outcomes + `text_quality` (derived), not directly from PDF/web labels.

PDF-scrapable audit scope (manual CODEX checks allowed):
- `contract_type`, `contract_type_raw`, `contract_type_evidence`
- `contract_subtype_raw`, `contract_subtype_evidence`
- `contract_subtype` (from PDF subtype semantics; note: code normalization may use `anno`)
- `duration_months`, `duration_raw`, `duration_evidence`
- `section_structure_department`, `section_evidence`
- `institute_cost_total_eur`, `institute_cost_yearly_eur`, `institute_cost_evidence`
- `gross_income_total_eur`, `gross_income_yearly_eur`, `gross_income_evidence`
- `net_income_total_eur`, `net_income_yearly_eur`, `net_income_monthly_eur`, `net_income_evidence`

Non-PDF-only fields (must be `NOT_REVIEWED` in CODEX column):
- `detail_id` (web key/context)
- `position_row_index` (derived from segmentation order)
- `text_quality` (derived classifier)
- `parse_confidence` (derived score)

Environment command rules (mandatory in this repo):
- Do NOT use `sqlite3` CLI (not available in this environment).
- Use `./.venv/bin/python` (not `python`) for all DB queries and helper scripts.
- For PDF text extraction, use one of:
  - `mutool draw -F txt data/pdf_cache/<detail_id>.pdf`
  - or project helper code that wraps mutool.

Comparison rules:
- If CODEX value is `NOT_REVIEWED` => `⚪`.
- Else compare normalized values:
  - trim spaces
  - case-sensitive text compare after trim
  - numeric compare by value (e.g. `2000` == `2000.0`)
  - `NULL` matches only `NULL`
- Set `✅` if match, else `❌`.

Execution:
1) Read existing markdown.
2) Confirm only the fixed canary list is audited: `4507, 4476, 4490, 4493, 4484, 4456, 4358, 4223, 4302, 4441, 4458`.
3) Validate provenance by reading these source files before declaring provenance updated:
   - `src/infn_jobs/store/spec/position_rows.py`
   - `src/infn_jobs/domain/position.py`
   - `src/infn_jobs/extract/parse/core/orchestrator.py`
   - `src/infn_jobs/extract/parse/core/execution_shared.py`
   - `src/infn_jobs/extract/parse/rules/contract_identity.py`
   - `src/infn_jobs/extract/parse/normalize/subtypes.py`
   - `src/infn_jobs/extract/parse/rules/duration.py`
   - `src/infn_jobs/extract/parse/rules/section.py`
   - `src/infn_jobs/extract/parse/rules/income.py`
   - `src/infn_jobs/extract/parse/fields/confidence.py`
   - `src/infn_jobs/pipeline/sync.py` (where `anno` is passed to parsing)
4) Re-derive field provenance from current code.
5) Update `Field provenance map` in this file and in `docs/audit_canariesmismatch.md`.
6) Query schema + row values from DB using `./.venv/bin/python` and sqlite3 module.
7) Read canary PDFs and fill CODEX values ONLY for PDF-scrapable fields.
8) For non-PDF-only fields, force `NOT_REVIEWED`.
9) Recompute comparison column.
10) Write updated `docs/audit_canariesmismatch.md`.

Output requirements:
- Apply the file edit directly.
- After editing, print a short summary:
  - whether provenance maps were updated in both files
  - checklist status for required provenance-validation files (all read vs missing)
  - which detail_ids were updated
  - count of `✅`, `❌`, `⚪` per detail_id
  - any fields left `NOT_REVIEWED`.
