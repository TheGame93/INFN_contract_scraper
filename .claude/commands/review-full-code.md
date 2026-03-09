You are doing a comprehensive audit of a completed Python project. Read ALL of the following before starting any analysis:

1. `CLAUDE.md` — conventions, architecture, all constraints
2. `docs/plan_desiderata.md` — what was planned (fields, rules, test plan)
3. `docs/plan_implementation.md` — how it was planned (file tree, function signatures, DB schema)
4. `docs/info_functions.md` — current function index (auto-generated)
5. `docs/step/planning_step.md` + all `docs/step/implement_stepN.md` files (steps 1–9) — what was supposed to be implemented in each step

Then read the full source tree under `src/infn_jobs/` and `tests/`.

---

## Audit Tasks

### 1. Completeness check
For every item in `plan_desiderata.md` and every sub-substep in the implement files, verify it is actually implemented. List any planned item that is missing or only partially done.

### 2. Architecture and dependency rule
Verify the dependency rule: `domain` has no imports from other layers. `cli` only calls `pipeline`. `pipeline` is the only layer that wires other layers. Flag any violation.

Check that shared utilities (`extract/pdf/`, `extract/parse/normalize/`, `fetch/client.py`) do not import from v1-specific modules (`fetch/listing/`, `fetch/detail/`, `extract/parse/fields/`, `pipeline/sync.py`).

### 3. Interface contracts
For each call site in `pipeline/sync.py`, verify the function signatures it calls match the actual definitions. Pay special attention to:
- `build_rows` return type: must be `tuple[list[PositionRow], str | None]`; the pipeline must unpack `pdf_call_title` from it and set it on `call` before calling `upsert_call`
- `upsert_call` and `upsert_position_rows` signatures
- `fetch_all_calls` → `CallRaw` list

### 4. CLAUDE.md constraint audit
Check every constraint in CLAUDE.md `## Key Conventions` against the actual code:
- All fields nullable (no crashes on missing HTML/PDF fields)
- Upsert idempotency (`detail_id` as key, `first_seen_at` immutability)
- `text_quality = no_text` → `pdf_fetch_status = ok`, 0 position_rows, not `parse_error`
- `parse_error` reserved for mutool non-zero exit only
- `--dry-run`: no `upsert_*` or `rebuild_curated` calls, PDFs still cached
- `--force-refetch`: re-downloads all PDFs even if cached
- HTTP: 1.0s sleep, max 3 retries with exponential backoff on 5xx, no retry on 4xx, correct User-Agent
- PDF URL resolution: absolute if starts with `http`, else join with BASE_URL origin only
- BeautifulSoup always receives `response.content` (bytes), never `response.text`
- `position_row_index` is 0-based and assigned by segment order
- `detail_url` constructed as `{BASE_URL}/dettagli_job.php?id={detail_id}`
- Logging: no `print()` in library code; all modules use `logging.getLogger(__name__)`

### 5. Field extraction logic
For each field extractor in `extract/parse/fields/`, check:
- Does it handle missing/malformed input without raising?
- Does it return `None` (not empty string, not 0) when the field is absent?
- Does `income.py` extract all 7 EUR fields with grouped evidence?
- Does `contract_type.py` store both canonical and raw values?
- Does subtype normalization handle `Fascia II → Fascia 2`, `Tipo A/B` with era-awareness (pre-2010 → NULL)?
- Does `confidence.py` NOT penalize NULL financial fields in old records?

### 6. Store layer
- Does `init_db` run idempotently (safe to call twice)?
- Does `position_rows_curated` VIEW exist and return the correct shape?
- Does `export_all` write exactly 4 CSV files to `data/exports/`?
- Does `rebuild_curated` correctly filter employment-like calls?

### 7. Dead code
Search for functions, classes, or imports that are defined but never called from any reachable code path. List them.

### 8. Test coverage gaps
For each module in `src/infn_jobs/`, check whether there is a corresponding test. List any module that has no test coverage at all and where the risk of a bug is non-trivial.

### 9. Known edge cases
Read `docs/known_edge_cases.md`. Verify that each documented edge case has either a fixture + test or a code comment explaining how it is handled.

---

## Output format

For each finding, report:
- **Category** (one of: Completeness / Architecture / Interface / Convention / Field Extraction / Store / Dead Code / Test Gap / Edge Case)
- **Severity**: `bug` (wrong behavior) | `gap` (missing but not crashing) | `smell` (suspicious but may be fine)
- **Location**: file and line number if applicable
- **Description**: what is wrong or missing
- **Fix**: concrete suggestion

At the end, produce a summary table with counts per category and severity.
