# Claude Review 2.2 — Deep Coherence Audit (Steps 6–9)

> **Base material:** `docs/codex_review_2.2.md` (Codex AI analysis of steps 6–9).
> **Scope:** expand, correct, and deepen every finding; add new findings Codex missed.
> **Authoritative anchor:** `docs/plan_desiderata.md`.
> **Cross-references used:** all `implement_step{1..9}.md`, `plan_implementation.md`, `CLAUDE.md`,
> `planning_step.md`, `policy_step.md`, `codex_review_1.md`, `codex_review_2.1.md`.

---

## Resolution Status (post-review update)

This review was written against the **original** versions of the planning files. Since then,
fixes from `claude_review_1.md` and `claude_review_2.1.md` have been applied. The table below
shows the current status of each finding.

| ID | Status | Notes |
|---|---|---|
| C1 | **Resolved** | `implement_step7.md` now has substep 7.1 (`pipeline/export.py`). `implement_step8.md` now calls `pipeline.export.run_export`. `plan_implementation.md` file tree updated. |
| C2 | **Resolved** | `policy_step.md` lines 154 and 242 now reference the auto-generation script. No manual-edit language remains. |
| C3 | **Resolved** | `implement_step6.md` now defines `position_rows_curated` as a VIEW (lines 37–83). CSV export queries the VIEW directly. |
| C4 | **Resolved** | `plan_desiderata.md` and `CLAUDE.md` now agree: `no_text` → 0 `position_rows`, `pdf_fetch_status = ok`. `implement_step5.md` returns `([], None)` for `no_text`. |
| C5 | **Resolved** | Renamed to `contract_type_raw` throughout. Added to `PositionRow` (step 2), `position_rows` schema (step 6), and field extractor (step 5). |
| H1 | **Resolved** | `implement_step6.md` line 88 documents that FK constraints are intentionally unenforced (schema-as-documentation). |
| H2 | **Partially resolved** | Test definition at line 212 is correct (`_is_noop`), but the **reference** at line 185 still says `_clears_rows`. Needs one-line fix. |
| H3 | **Resolved** | `planning_step.md` already trimmed to summary-only format. |
| H4 | **Unresolved** | Step 9 e2e test still only mocks `TextQuality.DIGITAL`. Needs `no_text` and `ocr_degraded` test paths. |
| H5 | **Resolved** | `implement_step3.md` line 31 now uses 4 `.parent` calls. |
| H6 | **Unresolved** | Step 6 curated filter notes don't document that the filter is functionally vacuous / future-proofing. |
| M1 | **Resolved** | `implement_step5.md` now has rate limiting inside `download()`. Step 7 line 114 documents this. |
| M2 | **Resolved** | Double `init_data_dirs()` call is documented as intentional in step 7 and step 8. |
| M3 | **Accepted** | Network dependency for step 9.2 is inherent to a scraper project. No change needed. |

**Remaining fixes needed:** H2 (one-line test name fix in step 6), H4 (e2e test coverage in step 9), H6 (curated filter documentation in step 6).

---

## Executive Verdict

Steps 6–9 are **partially coherent**. The core data flow is well-specified, but several
critical contradictions — CLI boundary violation, curated output schema mismatch, `no_text`
behavior conflict, and `source_contract_type` omission from upstream — remain unresolved and
directly impact the implementability and testability of these steps. Codex correctly identified
5 of the major issues. This review adds 8 new findings and substantially deepens all existing ones.

> **Post-review note:** Most findings above have been resolved by fixes from `claude_review_1.md`
> and `claude_review_2.1.md`. See the Resolution Status table above for current state. Only H2,
> H4, and H6 remain actionable.

---

## Compliance Matrix (Steps 6–9)

| Step | Status | Rationale |
|---|---|---|
| 6 | Non-compliant | Curated schema doesn't satisfy desiderata's denormalized output expectation; internal empty-list upsert contradiction; FK constraints are decorative without `PRAGMA foreign_keys = ON`; curated filter is functionally vacuous given the scraper's own tipo scope. |
| 7 | Partial | Pipeline wiring is well-specified but inherits unresolved `no_text` behavior; rate-limit responsibility for PDF downloads is ambiguous with Step 5; double `init_data_dirs()` is harmless but reveals unclear ownership. |
| 8 | Non-compliant | `cmd_export.py` directly calls `store.export.csv_writer.export_all()`, violating the `cli → pipeline only` rule in CLAUDE.md. |
| 9 | Partial | E2e test design is strong but does not cover `no_text`/`ocr_degraded` paths; `info_functions` process contradicts policy; full-run verification assumes live network which conflicts with reproducibility. |

---

## Findings

### Severity Legend

- **C** = Critical — contradictions that block correct implementation or produce ambiguous results.
- **H** = High — issues that cause semantic drift, unclear behavior, or incomplete coverage.
- **M** = Medium — inconsistencies that are confusing but have workable defaults.

---

### C1. CLI Boundary Violation in Step 8 Export Command

**Codex identified this. Expanded here.**

**The contradiction:**
- CLAUDE.md architecture rule: "`cli` only calls `pipeline`" (CLAUDE.md § Architecture, the
  dependency rule).
- `implement_step8.md` line 153: `cmd_export.py` imports
  `from infn_jobs.store.export.csv_writer import export_all` — a direct `cli → store` call.
- `plan_implementation.md` line 27: file tree documents `cmd_export.py # execute(args) → store.export`.
- `planning_step.md` line 87: `cli/cmd_export.py → store.export.csv_writer.export_all(...)`.

**Deeper analysis:**
The contradiction is not merely a documentation glitch. Step 8.4.1 provides the full
`execute()` body (lines 154–163): it calls `pipeline.curate.rebuild_curated(conn)` **and**
`store.export.csv_writer.export_all(conn, EXPORT_DIR)`. So the export command already uses
a pipeline wrapper for curation but bypasses it for the CSV write. This is architecturally
inconsistent — if `rebuild_curated` deserves a pipeline wrapper (Step 7.1), so does `export_all`.

**Two resolution paths:**
1. **Add `pipeline/export.py`** with a thin wrapper `run_export(conn, export_dir)` that calls
   both `rebuild_curated(conn)` and `export_all(conn, export_dir)`. Then `cmd_export.py` calls
   only pipeline. Consistent with the curation wrapper pattern.
2. **Relax CLAUDE.md** to say `cli` calls `pipeline` for sync, and may call `store.export`
   directly for export. Simpler, but sets a precedent that erodes the layer boundary.

**Recommendation:** Option 1. It costs 10 lines of code and preserves the architectural invariant.

---

### C2. `docs/info_functions.md` Process Conflict

**Codex identified this. Expanded here.**

**The contradiction:**
- CLAUDE.md § `docs/info_functions.md`: "It is auto-generated — do not edit it by hand."
  Run `python3 scripts/gen_info_functions.py` to regenerate.
- `policy_step.md` line 154: per sub-substep checklist, "`docs/info_functions.md` updated:
  add an entry for every new function or class."
- `policy_step.md` line 241: "Do not create a function without adding it to
  `docs/info_functions.md`."
- Step 9.3 (lines 126–142) correctly treats it as script-generated.

**Deeper analysis:**
The conflict is between two models:
- **Incremental manual model** (policy_step.md): update `info_functions.md` after every
  sub-substep. This means the file is hand-edited ~50+ times during implementation.
- **Batch generation model** (CLAUDE.md, Step 9.3): run the script once at project close
  (or whenever needed). The file is never hand-edited.

The incremental model is impractical because: (a) the generated format is complex (table per
function), (b) manual entries will diverge from what the script produces, (c) Step 9.3 will
overwrite all manual entries anyway.

**Resolution:** Amend `policy_step.md` to say: "Run `python3 scripts/gen_info_functions.py`
after any session that adds/removes/renames public functions. Do not edit the file by hand."
Remove the manual-entry language from the sub-substep and substep checklists (lines 154, 179,
241). This aligns policy with CLAUDE.md and Step 9.3.

---

### C3. Curated Schema vs. Desiderata Output Contract

**Codex identified this as C4. Expanded and deepened here.**

**The contradiction:**
- `plan_desiderata.md` § "Canonical Fields in `position_rows_curated`" (lines 153–210) lists
  call-level fields as part of the curated output: `source_tipo`, `listing_status`, `numero`,
  `anno`, `numero_posti_html`, `data_bando`, `data_scadenza`, `first_seen_at`, `last_synced_at`,
  `pdf_fetch_status`, `detail_url`, `pdf_url`, `pdf_cache_path`, `call_title`.
- `plan_implementation.md` line 238: "`calls_curated` and `position_rows_curated` share the
  same schemas — populated by the employment-like filter."
- `implement_step6.md` line 36: confirms identical schema.
- `implement_step6.md` line 229: CSV export uses `SELECT * FROM <table>` for position_rows.

**Deeper analysis:**
The desiderata envisions `position_rows_curated` as a **denormalized, analytics-ready** table
where each row carries its parent call's metadata. The implementation stores it as a **normalized**
copy of `position_rows` (same schema, filtered by tipo). The CSV export does not join the tables.

This means `position_rows_curated.csv` will be missing:
- `source_tipo`, `listing_status`, `anno` — required for any meaningful time-series analysis
- `call_title` — the derived `COALESCE(pdf_call_title, titolo)` field
- `numero_posti_html`, `data_bando`, `data_scadenza` — call-level metadata

An analyst receiving `position_rows_curated.csv` would need to manually join it with
`calls_curated.csv` on `detail_id` to reconstruct what the desiderata promised as the
canonical output. This defeats the "analytics-ready" purpose.

**Two resolution paths:**
1. **Denormalize the CSV export only:** Keep the DB schema normalized, but change the
   position_rows CSV export query to `SELECT pr.*, cr.source_tipo, cr.listing_status, cr.anno,
   ... FROM position_rows_curated pr JOIN calls_curated cr ON pr.detail_id = cr.detail_id`.
   This satisfies the desiderata without schema changes.
2. **Denormalize the curated table itself:** Add call-level columns to `position_rows_curated`
   and populate them in `rebuild_curated()`. More storage, but queries are simpler.

**Recommendation:** Option 1. It matches the desiderata's intent (analytics-ready CSV) without
changing the DB schema. Update `implement_step6.md` substep 6.7 to use a JOIN query for the
curated position_rows CSV.

---

### C4. `no_text` Behavior Is Self-Contradictory Across 4 Documents

**Codex identified this as H1. Elevated to Critical here.**

**The contradictions (all four are active simultaneously):**

| Document | Location | States |
|---|---|---|
| `plan_desiderata.md` | line 246 | `no_text` → 0 `position_rows`, `pdf_fetch_status = parse_error` |
| `implement_step5.md` | line 765 | `no_text` → still attempt extraction, assign `low` confidence (produces rows) |
| `implement_step5.md` | line 766 | empty text → return `([], None)` (no rows) |
| `implement_step7.md` | line 99 | success path sets `pdf_fetch_status = "ok"` after `build_rows` |
| `implement_step7.md` | line 110 | `build_rows` may return `[]` for `no_text` — skip upsert |
| `plan_desiderata.md` | line 269 | e2e expects `no_text` rows with `parse_confidence = low` |
| `plan_implementation.md` | line 285 | same expectation as desiderata e2e |

**Deeper analysis:**
There are actually *three* conflicting behaviors described:

1. **Desiderata test plan (line 246):** `no_text` = 0 rows + `parse_error`. This is the
   strictest interpretation: no_text PDFs are treated as parse failures.
2. **Step 5 row_builder (line 765):** `no_text` = attempt extraction → rows with all-None
   fields → `parse_confidence = low`. This produces *at least 1 row* (from `segment()` which
   always returns at least one element).
3. **Desiderata e2e (line 269):** expects rows with `parse_confidence = low` from `no_text`
   quality. Contradicts behavior #1.

The edge case is sharp: `text_quality = no_text` means <50 chars of garbage. `segment()` will
return `["<garbage>"]` (one segment). Extractors return all None. `score_confidence` assigns
`low`. Result: 1 `PositionRow` with everything None except `detail_id`, `position_row_index=0`,
`text_quality="no_text"`, `parse_confidence="low"`. This is behavior #2.

But behavior #1 says this should produce 0 rows and `pdf_fetch_status = parse_error` (not `ok`).

**Additionally:** Step 7 line 99 sets `pdf_fetch_status = "ok"` whenever `build_rows` succeeds
(no exception). Under behavior #2, a `no_text` PDF would get `pdf_fetch_status = "ok"` — but
the desiderata explicitly requires `parse_error` for `no_text`.

**Resolution options:**
1. **Follow desiderata line 246 strictly:** In `build_rows`, if `text_quality == "no_text"`,
   return `([], None)`. In `run_sync`, treat empty rows from a PDF that was successfully
   downloaded as `pdf_fetch_status = "parse_error"` when `text_quality == "no_text"`. Remove
   the conflicting e2e expectation from desiderata line 269.
2. **Follow behavior #2:** Keep rows with `low` confidence for `no_text`. Amend desiderata
   line 246 to remove "0 position_rows" and "parse_error" for `no_text`. Set
   `pdf_fetch_status = "ok"` since extraction technically succeeded.

**Recommendation:** Option 1 for `no_text` (truly empty PDFs shouldn't produce phantom rows),
but keep behavior #2 for `ocr_degraded` (degraded text may still yield partial data, and rows
with `low` confidence serve as audit trail). This means:
- `no_text` → `([], None)`, `pdf_fetch_status = "parse_error"`
- `ocr_degraded` → attempt extraction, rows with `low` confidence, `pdf_fetch_status = "ok"`

---

### C5. (NEW) `source_contract_type` Omission Propagates Into Steps 6–9

**Codex review 2.1 identified this as C3 for steps 1–5. Still unresolved in steps 6–9.**

- `plan_desiderata.md` line 106: "Extract **row-level** fields for each position entry:
  `source_contract_type` (if stated in PDF body)."
- No step (1–9) models, stores, or exports this field.
- `PositionRow` dataclass (Step 2) omits it.
- `position_rows` DB schema (Step 6) omits it.
- The desiderata explicitly names it as a row-level extraction target.

**Impact on steps 6–9:**
- Step 6 schema creation will silently omit a required field.
- Step 9 verification against desiderata will pass because the checklist doesn't test for this
  field, but the desiderata requirement is unmet.

**Resolution:** Either add `source_contract_type` to `PositionRow`, the DB schema, and a field
extractor — or explicitly de-scope it in `plan_desiderata.md` with a note explaining why
(e.g., `source_contract_type` is redundant with `contract_type` since both come from the PDF
body; or `source_tipo` from the listing is sufficient for v1).

---

### H1. Step 6 FK Constraints Are Decorative Without PRAGMA

**New finding — Codex missed this.**

- `implement_step6.md` lines 37, 199–200: FK constraints declared on `position_rows` and
  `position_rows_curated`, with careful ordering of INSERT/DELETE to respect them.
- **SQLite does not enforce foreign key constraints by default.** `PRAGMA foreign_keys = ON`
  must be executed on each connection.
- Neither `init_db()` (Step 6.1) nor `tests/conftest.py` `tmp_db` fixture (Step 6.2) enables
  this pragma.
- `cmd_sync.py` and `cmd_export.py` (Step 8) create connections without enabling it.

**Impact:** The FK ordering discipline in `rebuild_curated()` (delete curated rows before
curated calls, insert calls before rows) is unnecessary at runtime but correct for correctness.
However, orphaned `position_rows` (rows referencing a non-existent `detail_id` in `calls_raw`)
would silently persist without any constraint error.

**Resolution:** Add `conn.execute("PRAGMA foreign_keys = ON")` in `init_db()` after connection
is opened, or document that FK constraints are intentionally unenforced (schema documentation
only). Given that the pipeline guarantees `upsert_call` before `upsert_position_rows`, this is
low-risk, but the schema's FK declarations create an expectation that enforcement exists.

---

### H2. Empty-List `upsert_position_rows` Semantics Contradiction

**Codex identified this as H3. Refined here.**

- `implement_step6.md` line 133: test name `test_upsert_position_rows_empty_list_clears_rows`
  — implies empty list clears existing rows.
- `implement_step6.md` line 135: notes say "If `rows` is empty, do nothing and return (no
  detail_id to clear)."
- `implement_step6.md` line 160: test `test_upsert_position_rows_empty_list_is_noop` — aligned
  with the noop behavior.

The test name at line 133 contradicts the implementation notes and the test at line 160.

**Deeper analysis:** The noop behavior is correct for the pipeline. When `build_rows` returns
`[]` (e.g., for `no_text`), there's no `detail_id` in the empty list to key the DELETE on.
The pipeline guards with `if rows:` (Step 7 line 107), so the function is never called with
an empty list in practice. But the test name at line 133 would lead an implementer to write
"clear rows for a given detail_id" behavior instead.

**Resolution:** Rename the test at line 133 to `test_upsert_position_rows_empty_list_is_noop`
(matching line 160) or remove it entirely since line 160 already covers this case.

---

### H3. Master Tracker Violates Policy Format Rules

**Codex identified this as H2. Confirmed here.**

- `policy_step.md` line 67: "Does NOT contain implementation detail — only the summary and a
  link to `implement_stepN.md`."
- `planning_step.md` lines 39–94: contains function signatures, command arguments, return types,
  and implementation notes (e.g., line 63: `build_rows(text, detail_id, text_quality, anno) ->
  tuple[list[PositionRow], str | None]`).

**Resolution:** Strip `planning_step.md` step index entries to one-line summaries with a link
to the implement file. Example:
```
[ ] 5.16 Row builder — `implement_step5.md` § 5.16
```

---

### H4. (NEW) Step 9 E2E Test Does Not Cover `no_text` or `ocr_degraded` Paths

- `implement_step9.md` line 51: mock `extract_text` always returns `(MULTI_TEXT, "digital")`.
- No test varies `text_quality` to exercise `no_text` or `ocr_degraded` code paths.
- `plan_desiderata.md` lines 244–246, 269: explicitly require testing these paths.

**Impact:** The e2e test validates the happy path but cannot detect regressions in:
- `no_text` → 0 rows / parse_error (if behavior #1 is chosen)
- `ocr_degraded` → low confidence scoring
- `text_quality` column correctness in position_rows

**Resolution:** Add parametrized e2e tests or additional test cases where the `extract_text`
mock returns `("", "no_text")` and `("<garbled>", "ocr_degraded")`. Assert expected row counts
and `parse_confidence` values. This does not require new fixture files — just different mock
return values.

---

### H5. (NEW) Step 3 `_PROJECT_ROOT` Resolution Error in Specification

- `implement_step3.md` line 31 (the Write block): `_PROJECT_ROOT: Path = Path(__file__).parent.parent.parent`
- `implement_step3.md` line 43 (Notes): correctly identifies that 3 parents go
  `config/ → infn_jobs/ → src/` — NOT the project root. States 4 parents are needed:
  `config/ → infn_jobs/ → src/ → project_root`.

**The Write block and the Notes contradict each other.** The Write block has 3 `.parent` calls;
the Notes say 4 are needed. The Notes are correct.

**Impact:** If an implementer copies the Write block verbatim, `DB_PATH` will resolve to
`src/data/infn_jobs.db` instead of `<project_root>/data/infn_jobs.db`. All data paths will
be wrong.

**Resolution:** Fix the Write block in `implement_step3.md` line 31 to use
`Path(__file__).parent.parent.parent.parent`. The Notes already explain why.

---

### H6. (NEW) Curated Filter Is Functionally Vacuous

- `implement_step6.md` line 192: curated filter: `WHERE source_tipo IN ('Borsa', 'Incarico
  di ricerca', 'Incarico Post-Doc', 'Contratto di ricerca', 'Assegno di ricerca')`.
- `config/settings.py` TIPOS (Step 3): the scraper *only* fetches these 5 tipos.
- Therefore `calls_raw` will only ever contain rows with `source_tipo` IN those 5 values.
- `calls_curated` will be identical to `calls_raw` in all cases.

**Impact:** The curated tables add storage and computation cost but provide zero analytical
filtering. The `rebuild_curated()` function, its tests (Step 6.9), and the separate curated
CSVs are all technically redundant.

**Contextual note:** The desiderata line 135 mentions "Exclude prize-only/non-employment
notices unless linked to an extracted job row" — implying there might be non-employment records.
But since the scraper only fetches the 5 employment-like tipos, no such records will exist.

**Resolution options:**
1. **Keep as future-proofing:** if v2 adds more tipos (e.g., prizes, awards), the curated
   filter becomes meaningful. Document this explicitly.
2. **Add content-based filtering:** filter by `contract_type` presence or `pdf_fetch_status`
   quality, making the curated set a stricter subset.
3. **Remove curated tables from v1:** export only raw tables. Simpler, no false promise of
   curation. Add curated when the filter criteria become non-trivial.

**Recommendation:** Option 1 (keep, but document). The implementation cost is low, and the
test coverage for `rebuild_curated()` validates the pattern for v2. Add a comment in
`curate.py` explaining that the filter becomes meaningful when new source types are added.

---

### M1. PDF Download Rate-Limit Responsibility Is Ambiguous

**Codex identified this. Refined here.**

- `plan_desiderata.md` line 62: "Sleep 1.0 s between every request (active + expired listings,
  detail pages, PDF downloads)."
- `implement_step7.md` line 114: "Rate limiting: enforced inside `fetch_all_calls` and
  `download` (both call `time.sleep(RATE_LIMIT_SLEEP)` between requests)."
- `implement_step5.md` lines 43–61: `download()` spec does not mention rate-limit sleep.
- `implement_step4.md` line 36: "Rate-limit sleep is NOT enforced inside the session — it is
  the caller's responsibility (orchestrator sleeps between requests)."

**Analysis:** Step 7 claims `download()` enforces rate limiting internally. Step 5 (which
defines `download()`) doesn't mention it. Step 4 says rate limiting is the caller's responsibility.

**Resolution:** Either:
- Add `time.sleep(RATE_LIMIT_SLEEP)` inside `download()` before each HTTP request, and update
  `implement_step5.md` to document this. Or:
- Have `run_sync()` in Step 7 sleep before each `download()` call, and amend Step 7 line 114
  to say rate limiting for PDFs is handled in the pipeline, not inside `download()`.

The first option is cleaner — `download()` as a self-contained, rate-limited HTTP operation.

---

### M2. (NEW) Step 7 Double `init_data_dirs()` Call

- `implement_step8.md` line 72: `cli/main.py` `run()` calls `init_data_dirs()` at startup.
- `implement_step7.md` line 70: `run_sync()` also calls `init_data_dirs()` as its first action.

Both calls are idempotent and harmless. But the duplication signals unclear ownership:
- Is `init_data_dirs()` a CLI responsibility (initialize before any command)?
- Or a pipeline responsibility (ensure dirs exist before I/O)?

**Resolution:** Keep both calls (belt-and-suspenders is fine for directory creation), but
clarify in CLAUDE.md: "Called once at CLI startup; also called defensively inside `run_sync()`
for standalone/testing use."

---

### M3. (NEW) Step 9 Verification Requires Live Network

- `implement_step9.md` lines 98–112 (substep 9.2): 8 of 9 verification items require a live
  `data/infn_jobs.db` populated by a real `sync` run against `jobs.dsi.infn.it`.
- This means Step 9.2 cannot be completed in a CI environment or on a machine without network
  access.
- Item 9 (`pytest tests/ -v`) is network-independent.

**Impact:** Step 9.2 is the only verification gate for the complete pipeline against real data.
If the live site changes structure, this step may fail without any code change.

**Resolution:** This is acceptable for v1 (the project is a scraper, so live verification is
inherently necessary). Document in `implement_step9.md` that 9.2 is a manual, network-dependent
gate and will not be part of automated CI. The `pytest` suite (9.2 item 9) remains the automated
regression check.

---

## Summary of Resolutions Needed

| ID | Severity | Fix Location | One-Line Summary |
|---|---|---|---|
| C1 | Critical | `implement_step7.md`, `implement_step8.md`, `plan_implementation.md` | Add `pipeline/export.py` wrapper; `cmd_export` calls only pipeline |
| C2 | Critical | `policy_step.md` | Replace manual `info_functions` updates with script-run instruction |
| C3 | Critical | `implement_step6.md` § 6.7, `plan_implementation.md` | Use JOIN query for curated position_rows CSV export |
| C4 | Critical | `plan_desiderata.md`, `implement_step5.md`, `implement_step7.md` | Decide `no_text` → 0 rows + parse_error (line 246) vs rows + low; update all docs |
| C5 | Critical | `plan_desiderata.md` or steps 2/5/6 | De-scope `source_contract_type` or add it to dataclass/schema/extractor |
| H1 | High | `implement_step6.md` § 6.1 | Add `PRAGMA foreign_keys = ON` or document unenforced FKs |
| H2 | High | `implement_step6.md` § 6.4/6.5 | Fix contradictory test name `_clears_rows` → `_is_noop` |
| H3 | High | `planning_step.md` | Strip to summary-only per policy |
| H4 | High | `implement_step9.md` § 9.1 | Add e2e tests for `no_text` and `ocr_degraded` mock paths |
| H5 | High | `implement_step3.md` § 3.1 | Fix `_PROJECT_ROOT` to use 4 `.parent` calls, not 3 |
| H6 | High | `implement_step6.md` § 6.6 | Document that curated filter is future-proofing, not active filtering |
| M1 | Medium | `implement_step5.md` § 5.1, `implement_step7.md` | Clarify rate-limit ownership for PDF downloads |
| M2 | Medium | CLAUDE.md | Clarify `init_data_dirs()` double-call is intentional |
| M3 | Medium | `implement_step9.md` § 9.2 | Document network dependency for live verification |

---

## Cross-Cutting Issues Still Open From Reviews 1 and 2.1

These were identified in earlier reviews and remain unresolved. They affect steps 6–9:

1. **C1 from review 1 = C1 here:** CLI boundary violation. Same issue, same fix needed.
2. **C3 from review 2.1 = C5 here:** `source_contract_type` missing. Needs a decision.
3. **H1 from review 2.1 = C4 here:** `no_text` contradiction. Now elevated to Critical because
   it directly blocks Step 7 and Step 9 implementation with conflicting acceptance criteria.
4. **H2 from review 2.1 = H3 here:** planning_step.md format. Cosmetic but accumulates
   confusion across sessions.

---

## Assumptions

- `docs/plan_desiderata.md` is authoritative for requirement intent where documents conflict.
- This review is documentation-only — no code or implementation files were modified.
- Findings from `codex_review_2.1.md` and `codex_review_1.md` are cross-referenced where
  they carry forward into steps 6–9.
- All line references are to the file versions read during this session (2026-03-08).
