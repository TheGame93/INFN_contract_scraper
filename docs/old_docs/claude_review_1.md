# Claude Review 1 — Top-Down Planning Coherence Audit

## Scope

This review expands on `docs/codex_review_1.md` (Codex Review 1, Revision 2).
Authoritative goal document: `docs/plan_desiderata.md`.

Reviewed documents:
- `docs/plan_desiderata.md` (the goal)
- `docs/plan_implementation.md` (the plan)
- `CLAUDE.md` (AI instruction file)
- `docs/step/planning_step.md` (master tracker)
- `docs/step/policy_step.md` (step execution rules)

This audit is structured as:
1. **Part A** — Does `plan_implementation` satisfy `plan_desiderata`?
2. **Part B** — Does `CLAUDE.md` address the weak spots of `plan_implementation`?
3. **Part C** — Are `plan_implementation` and `CLAUDE.md` coherent?
4. **Part D** — Does `planning_step.md` comply with all three?
5. **Part E** — Does `policy_step.md` comply with all three?
6. **Part F** — Cross-cutting issues
7. **Decisions required** — Actionable resolution list

Severity levels: **CRITICAL** (blocks correct implementation or creates contradictions that produce wrong code), **HIGH** (ambiguity that will cause inconsistent implementation across sessions), **MEDIUM** (friction or minor incoherence), **LOW** (cosmetic or style).

---

## Part A — Does `plan_implementation` satisfy `plan_desiderata`?

**Verdict: Partially compliant — 4 critical gaps, several high-severity omissions.**

### A-C1. CRITICAL — `source_contract_type` missing from schema and file tree

Desiderata `plan_desiderata.md:106` requires row-level extraction of `source_contract_type` ("if stated in PDF body"). This is a distinct field from `contract_type` — it captures the literal contract type string found in the PDF, as opposed to the normalized `contract_type` enum.

`plan_implementation.md` schema (`position_rows`, lines 204–235) has no `source_contract_type` column. The field extractor list in the file tree (lines 66–71) does not mention it. The step plan (`planning_step.md`) also omits it entirely.

**Impact:** If this field is required in v1, every downstream document needs updating: schema, dataclass, field extractor, evidence column, CSV export. If it was a desiderata mistake and `contract_type` + `contract_type_evidence` already covers the need, desiderata should be amended.

**Recommendation:** Clarify intent. If `source_contract_type` is the raw/unnormalized contract type text, it mirrors the `contract_subtype` / `contract_subtype_raw` pattern. In that case, rename to `contract_type_raw` for consistency and add it alongside `contract_type` in the schema. If it is redundant with `contract_type_evidence`, remove it from desiderata.

### A-C2. CRITICAL — `position_rows_curated` output contract is underspecified

Desiderata `plan_desiderata.md:153–210` defines `position_rows_curated` as a flat analytical table containing **both** call-level metadata (linkage/status fields, call metadata from HTML, source refs) **and** row-level analytics fields. This is a denormalized analytical view.

`plan_implementation.md:238` says `calls_curated` and `position_rows_curated` **share the same schemas** as their raw counterparts. The raw `position_rows` schema (lines 204–235) contains only row-level fields — no call-level metadata, no `listing_status`, no `anno`, no `numero`, no `pdf_fetch_status`.

This means:
- If curated tables literally share raw schemas → `position_rows_curated` lacks the call-level columns desiderata requires.
- If curated tables are denormalized views → the "shares same schema" statement is wrong and the actual schema must be defined.

The CSV export step will be forced to make an architectural decision that should have been made in the plan.

**Recommendation:** Define `position_rows_curated` explicitly. Two options:
1. **View/query approach:** `position_rows_curated` is a SQL VIEW joining `position_rows` with `calls_raw` (or `calls_curated`), producing the flat analytical shape desiderata describes. The CSV writer queries this view.
2. **Materialized table approach:** `position_rows_curated` is a physical table with the full denormalized schema from desiderata. `rebuild_curated()` populates it via INSERT...SELECT with JOIN.

Option 1 is simpler and avoids data duplication. Either way, the schema must be written out explicitly.

### A-C3. CRITICAL — `no_text` behavior is self-contradictory in desiderata (confirmed)

Codex flagged this (H1). Expanding with precise locations:

- `plan_desiderata.md:246`: "PDF with zero extractable text → `text_quality = no_text`, **0 `position_rows`**, `pdf_fetch_status = parse_error`."
- `plan_desiderata.md:269`: "`text_quality` values present in output; `ocr_degraded` or `no_text` **rows** have `parse_confidence = low`."

These are mutually exclusive. If `no_text` produces 0 rows, there are no rows to have `parse_confidence = low`. If `no_text` produces rows with `parse_confidence = low`, the test at line 246 is wrong.

Additionally, setting `pdf_fetch_status = parse_error` for `no_text` conflates "PDF was downloaded successfully but contains no text" with "PDF extraction tool failed." A `no_text` PDF is not a parse *error* — mutool succeeded, the PDF simply has no extractable text (common for scanned-only PDFs without OCR layer).

**Recommendation:**
- `no_text` → 0 `position_rows` (no data to extract), `pdf_fetch_status = ok` (download and mutool both succeeded).
- Remove the expectation that `no_text` rows exist with `parse_confidence = low` — there are no rows.
- If the PDF is `ocr_degraded`, produce 1 row with whatever was extracted (possibly all NULL fields), `parse_confidence = low`.
- Reserve `parse_error` for actual mutool failures (non-zero exit code, crash).

### A-C4. HIGH — Evidence granularity mismatch

Desiderata `plan_desiderata.md:122,208` says "raw evidence snippets for **every** parsed field." The phrasing "each field" suggests per-field evidence.

Schema in `plan_implementation.md:223–231` groups evidence into:
- `contract_type_evidence` (covers `contract_type`)
- `contract_subtype_evidence` (covers `contract_subtype` + `contract_subtype_raw`)
- `duration_evidence` (covers `duration_months` + `duration_raw`)
- `section_evidence` (covers `section_structure_department`)
- `institute_cost_evidence` (covers `institute_cost_total_eur` + `institute_cost_yearly_eur`)
- `gross_income_evidence` (covers `gross_income_total_eur` + `gross_income_yearly_eur`)
- `net_income_evidence` (covers `net_income_total_eur` + `net_income_yearly_eur` + `net_income_monthly_eur`)

This is 7 evidence columns for 16 extracted fields. The grouping is **reasonable** because related fields (e.g., `gross_income_total_eur` and `gross_income_yearly_eur`) are typically extracted from the same text snippet. However, desiderata says "every parsed field" which could be read as requiring 16 evidence columns.

**Recommendation:** Accept the grouped evidence approach (7 columns) as sufficient — it captures the source text for auditability without excessive column bloat. Amend desiderata line 208 to say "evidence snippet per field group" rather than "each field" to remove ambiguity.

### A-H1. HIGH — `call_title` derivation logic is specified but not in schema

Desiderata `plan_desiderata.md:189` defines `call_title` as "prefer `pdf_call_title`; fallback to `titolo` from detail page." Implementation `plan_implementation.md:240` correctly notes this is a derived CSV-only field via `COALESCE(pdf_call_title, titolo)`.

However, neither document specifies **where** this COALESCE lives. Is it:
- In the CSV writer SQL query?
- In `rebuild_curated()` as a computed column in `position_rows_curated`?
- In `row_builder.py` at extraction time?

Since `pdf_call_title` lives on `calls_raw` and `titolo` also lives on `calls_raw`, the COALESCE must happen in a JOIN query — which circles back to A-C2 (the curated output shape).

**Recommendation:** Place the `COALESCE` in the curated view/query that joins `position_rows` with `calls_raw`. This naturally resolves both `call_title` derivation and the denormalized output shape.

### A-H2. HIGH — Pagination fallback procedure is mentioned but not operationalized

Desiderata `plan_desiderata.md:67` says: "If a listing returns zero rows, check manually for pagination params and update `url_builder.py` accordingly. Document in `docs/known_edge_cases.md`."

`plan_implementation.md` does not mention pagination at all. `CLAUDE.md` does not mention it. The step plan does not include a verification sub-substep for zero-row listings.

**Impact:** If a tipo returns zero rows during Step 4 implementation, the session has no explicit procedure to follow.

**Recommendation:** Add a note in `plan_implementation.md` under the `fetch/` layer description. Add a verification sub-substep in Step 4 (after 4.4) that checks listing row counts are non-zero for all 5 tipos.

### A-M1. MEDIUM — `pdf_cache_path` storage is implicit

Desiderata `plan_desiderata.md:183` lists `pdf_cache_path` as a field in the canonical output. Schema in `plan_implementation.md:192` includes it in `calls_raw`. But no document specifies **when** it is set — is it set by the downloader? By the pipeline? What value does it store — relative path, absolute path?

**Recommendation:** Specify in `plan_implementation.md` that `pdf_cache_path` is set by `pipeline/sync.py` after a successful download, storing the relative path from project root (e.g., `data/pdf_cache/1234.pdf`). This is a minor gap but will cause a question during implementation.

### A-M2. MEDIUM — `detail_url` construction is unspecified

Desiderata `plan_desiderata.md:181` lists `detail_url` as "constructed from `detail_id`". Neither `plan_implementation.md` nor `CLAUDE.md` specifies the URL template. It should be `{BASE_URL}/dettagli_job.php?id={detail_id}` but this is never stated.

**Recommendation:** Add to `config/settings.py` description or `CLAUDE.md` conventions.

---

## Part B — Does `CLAUDE.md` address the weak spots of `plan_implementation`?

**Verdict: Good coverage of operational risks, but misses several desiderata-specific constraints.**

### What CLAUDE.md covers well:
- Character encoding (`response.content` not `response.text`) — addresses a real implementation trap.
- HTTP rate limit and retry policy — matches desiderata exactly.
- PDF URL resolution — addresses an ambiguity in implementation plan.
- `parse_confidence` semantics — correctly states "behavioral only."
- `text_quality` classification location — pins it to `extract/pdf/mutool.py`.
- Italian number format — clear normalization rule.
- Date format — clear.
- Subtype normalization — covers both canonical and raw, era-aware.
- `position_row_index` stability — critical for v2 FK.
- `detail_id` as stable FK — critical for v2.
- SQLite connection lifecycle — prevents transaction confusion.
- `build_rows` return type — prevents a common misunderstanding.
- `fetch_all_calls` conversion — clarifies orchestrator behavior.
- Logging standard — comprehensive.

### B-H1. HIGH — Missing 4xx handling policy

Desiderata `plan_desiderata.md:63` says: "Fail loudly on 4xx (log + set `pdf_fetch_status = download_error`)." CLAUDE.md mentions "Max 3 retries with exponential backoff on 5xx" but says nothing about 4xx behavior. A session implementing the HTTP client might retry 4xx errors (wrong) or silently skip them (wrong — should log + set status).

**Recommendation:** Add to CLAUDE.md HTTP rate limit convention: "Do not retry 4xx errors. Log at WARNING and set `pdf_fetch_status = download_error`."

### B-H2. HIGH — Missing TIPOS verification gate

Desiderata `plan_desiderata.md:69–75` explicitly says: "the exact string passed to `?tipo=` must be confirmed against the live site" and "Update `config/settings.py` TIPOS dict with verified values **before** implementing `url_builder.py`."

CLAUDE.md does not mention this verification gate. The step plan includes it (Step 3.3) but CLAUDE.md should reinforce it as a convention since it's a prerequisite that affects all downstream fetch logic.

**Recommendation:** Add a note under Key Conventions: "TIPOS values must be verified against the live site before Step 4. See Step 3.3."

### B-M1. MEDIUM — Missing pagination fallback

(Same as A-H2.) CLAUDE.md should mention the zero-row check procedure since it's an operational guardrail for any session doing fetch work.

### B-M2. MEDIUM — `dry_run` semantics not specified

CLAUDE.md mentions `--dry-run` as "parse only, no DB writes" but doesn't specify what **does** happen: Does it still fetch from the network? Does it download PDFs? Does it log what *would* be written?

Desiderata `plan_desiderata.md:148` just says "parse only, no DB writes."

**Recommendation:** Specify in CLAUDE.md: `--dry-run` fetches and parses normally but skips all `upsert_*` and `rebuild_curated` calls. PDFs are still downloaded and cached (network I/O is allowed in dry run). Logs show what would be upserted.

---

## Part C — Are `plan_implementation` and `CLAUDE.md` coherent?

**Verdict: Not fully coherent — 2 direct contradictions, 2 ambiguities.**

### C-C1. CRITICAL — CLI boundary rule contradiction

**CLAUDE.md line 60 (architecture section):** "`cli` only calls `pipeline`."

**`plan_implementation.md` line 27:** `cmd_export.py` → `store.export` (direct call, bypassing pipeline).

**`plan_implementation.md` line 168:** `export-csv` command maps to `cli/cmd_export.py` which "Read DB → write 4 CSV files" — implying direct `store` access.

**`planning_step.md` line 87:** Step 8.4 confirms `cmd_export.py` → `store.export.csv_writer.export_all(...)`.

These three sources agree with each other but contradict CLAUDE.md. The contradiction is between CLAUDE.md's strict "`cli` only calls `pipeline`" rule and the practical design where `export-csv` doesn't need pipeline orchestration.

**Analysis:** The strict rule makes sense for `sync` (which requires multi-layer orchestration). For `export-csv`, routing through pipeline would mean creating a `pipeline/export.py` that is a trivial pass-through to `store/export/csv_writer.py` — unnecessary indirection.

**Recommendation:** Two options:
1. **Relax CLAUDE.md:** Change to "`cli` calls `pipeline` for orchestration commands; may call `store.export` directly for read-only export commands." Update architecture section.
2. **Add pipeline wrapper:** Create `pipeline/export.py` with a thin `run_export(conn, export_dir)` that calls `rebuild_curated(conn)` then `export_all(conn, export_dir)`. This actually adds value: it ensures curated tables are fresh before export.

Option 2 is better — it ensures `export-csv` always rebuilds curated tables first, which is correct behavior. And it preserves the clean "`cli` only calls `pipeline`" rule.

### C-C2. CRITICAL — `pipeline/curate.py` vs `store/export/curate.py` duplication

`plan_implementation.md` file tree has **two** curate locations:
- `store/export/curate.py` (line 86): "SQL for curated filtering + `rebuild_curated(conn)`"
- `pipeline/curate.py` (line 92): "`rebuild_curated(conn)` — employment-like filter logic"

Both files define `rebuild_curated(conn)`. `planning_step.md` confirms:
- Step 6.6: `rebuild_curated(conn)` in store layer
- Step 7.1: `pipeline/curate.py` — "thin wrapper calling `store/export/curate.py`"

So `pipeline/curate.py` is a wrapper. But the file tree comments imply both contain the actual logic. And having a function with the same name in two modules is confusing.

**Recommendation:** Either:
1. Keep `rebuild_curated` only in `store/export/curate.py`. Pipeline imports it directly. No `pipeline/curate.py` file.
2. If you want a pipeline-level abstraction, name it differently: `pipeline/curate.py` has `refresh_curated_tables(conn)` which calls `store.export.curate.rebuild_curated(conn)`.

Option 1 is simpler and matches the "one concern per file" principle.

### C-H1. HIGH — Dependency direction wording is ambiguous

`plan_implementation.md:11`: "Dependency direction: `domain` ← `pipeline` ← `cli`. Infrastructure (`fetch`, `extract`, `store`) implements domain interfaces."

This arrow notation is confusing. Does `domain ← pipeline` mean "domain depends on pipeline" or "pipeline depends on domain"? In standard dependency notation, arrows usually point from dependent to dependency. But in import notation, arrows point the other direction.

CLAUDE.md states it more clearly: "`domain` has no dependencies. Everything else may depend on `domain` and `config`. `pipeline` is the only layer that wires other layers together. `cli` only calls `pipeline`."

But `plan_implementation.md` adds a concept CLAUDE.md doesn't mention: "Infrastructure implements domain interfaces." This implies domain defines abstract interfaces that fetch/extract/store implement — a ports-and-adapters pattern. But no interfaces are defined in `domain/`. The domain layer contains only dataclasses and enums.

**Recommendation:** Remove "implements domain interfaces" from `plan_implementation.md`. The actual pattern is simpler: domain defines data shapes, infrastructure layers produce/consume those shapes, pipeline wires them. No interfaces needed.

### C-M1. MEDIUM — `pdf_call_title` flow described differently

CLAUDE.md (build_rows return type convention): "The second element is `pdf_call_title` (call-level, from the PDF body). The pipeline (`run_sync`) unpacks it, sets `call.pdf_call_title`, then calls `upsert_call`. Never store `pdf_call_title` inside `PositionRow`."

`plan_implementation.md:63–64`: Same description in file tree comment.

`planning_step.md:80` (Step 7.3): "unpack `build_rows` tuple to get `pdf_call_title`, set on `CallRaw` before `upsert_call`"

These are **coherent** — included here to confirm alignment. This is a positive finding.

---

## Part D — Does `planning_step.md` comply with desiderata/implementation/CLAUDE?

**Verdict: Partially compliant — inherits critical gaps from implementation plan, plus structural violations.**

### D-C1. CRITICAL — Inherits all A-section gaps

`planning_step.md` step plan inherits every gap from `plan_implementation.md`:
- No `source_contract_type` extraction step
- No `position_rows_curated` denormalized schema definition step
- No `no_text` behavior clarification

These must be resolved at the `plan_implementation.md` level first, then reflected in step plan.

### D-H1. HIGH — Violates `policy_step.md` scope rule

`policy_step.md:67`: `planning_step.md` "Does NOT contain implementation detail — only the summary and a link to `implement_stepN.md`."

`planning_step.md` lines 39–94 contain extensive implementation detail:
- Function signatures (`build_urls(tipo) -> list[str]`)
- File paths (`fetch/orchestrator.py`)
- Parameter types (`conn, call: CallRaw`)
- Return types (`tuple[list[PositionRow], str | None]`)
- Behavioral notes ("second element is `pdf_call_title`; pipeline uses it to update `CallRaw` before upsert")

This turns the master tracker into a partial duplicate of `implement_stepN.md` files, violating the policy's "short and scannable" intent.

**Recommendation:** Reduce each step entry to one line:
```
[ ] 4.1 HTTP client with retry/rate-limit
[ ] 4.2 Listing URL builder
```
Move all signatures, file paths, and behavioral notes to `implement_stepN.md` files.

### D-H2. HIGH — `Currently Active` pointer granularity mismatch

`planning_step.md:12`: "Next to start: `1.1.1` — Create `pyproject.toml`"

But the Step Index (lines 18–94) only tracks at substep level (`1.1`, `1.2`, ...). Sub-substep numbers (`1.1.1`) are not listed here — they exist only in `implement_stepN.md`.

This means:
- The pointer says "go to 1.1.1"
- The index shows "1.1" with a `[ ]`
- You must open `implement_step1.md` to find 1.1.1

This is actually correct behavior per the policy (the pointer directs you to the implement file). But the granularity gap is confusing when the index includes implementation detail that makes it *look* like sub-substeps should be tracked here too.

**Recommendation:** This resolves itself if D-H1 is fixed. Keep the pointer at sub-substep granularity. Keep the index at substep level only.

### D-M1. MEDIUM — Step 8.4 contradicts CLAUDE.md (inherits C-C1)

Step 8.4: `cmd_export.py` → `store.export.csv_writer.export_all(...)`.
CLAUDE.md: `cli` only calls `pipeline`.

Inherited from C-C1. Fix at source.

### D-M2. MEDIUM — Step 9.3 contradicts CLAUDE.md on info_functions ownership

Step 9.3: "Update `docs/info_functions.md` with all implemented functions" (manual action).
CLAUDE.md: `info_functions.md` is "auto-generated — do not edit it by hand."

If it's auto-generated, Step 9.3 should say "Run `python3 scripts/gen_info_functions.py`" not "Update."

**Recommendation:** Change Step 9.3 wording to "Regenerate `docs/info_functions.md` by running `python3 scripts/gen_info_functions.py`."

---

## Part E — Does `policy_step.md` comply with desiderata/implementation/CLAUDE?

**Verdict: Partially compliant — strong execution discipline, but 2 conflicts with CLAUDE.md.**

### E-C1. CRITICAL — `info_functions.md` ownership conflict

`policy_step.md:154`: After each sub-substep, "`docs/info_functions.md` updated: add an entry for every new function or class."
`policy_step.md:179`: After each substep, "verify all functions in this substep have entries."
`policy_step.md:241`: "Do not create a function without adding it to `docs/info_functions.md`."

`CLAUDE.md:115–121`: "`docs/info_functions.md` is auto-generated — do not edit it by hand." Run `python3 scripts/gen_info_functions.py`.

These are directly contradictory. Policy says manually add entries after each sub-substep. CLAUDE.md says never edit by hand, use the generator script.

**Impact:** A session following policy will manually edit the file. A session following CLAUDE.md will run the script. The manual edits will be overwritten next time the script runs.

**Recommendation:** Choose one model:
1. **Auto-generated (CLAUDE.md is correct):** Remove all manual-update references from `policy_step.md`. Replace with "Run `python3 scripts/gen_info_functions.py` at the end of each step." Not after every sub-substep — that's too frequent and the script handles it.
2. **Manual (policy is correct):** Remove the auto-generation claim from `CLAUDE.md`. Delete or repurpose `scripts/gen_info_functions.py`.

Option 1 is clearly better — auto-generation is less error-prone and doesn't burden each sub-substep.

### E-H1. HIGH — Sub-substep definition doesn't match reality

`policy_step.md:43`: "A sub-substep is the smallest unit of work: one file created or one function added."

But `planning_step.md` includes sub-substeps that are verification actions, not file/function writes:
- Step 1.2: "Venv setup verification" (shell command, no file written)
- Step 1.6: "Smoke check: import without errors" (shell command)
- Step 3.3: "Verify TIPOS URL params against live site" (manual check)

**Recommendation:** Broaden the definition: "A sub-substep is the smallest unit of work: one file created, one function added, or one verification action performed."

### E-M1. MEDIUM — Session-reading guidance tension

`CLAUDE.md:34` (docs section): "Always read the relevant doc before starting work on a subsystem."
`policy_step.md:130`: "Do not re-read the full desiderata or implementation plan unless a specific field is unclear."

These aren't strictly contradictory — "relevant doc" could mean just the step file, not desiderata. But a session working on the fetch layer might interpret CLAUDE.md as requiring a re-read of `plan_desiderata.md` sections about fetch, while policy says don't bother.

**Recommendation:** Clarify in policy: "Read the relevant `implement_stepN.md` file. Refer to `plan_desiderata.md` or `plan_implementation.md` only when the step file doesn't answer a specific question."

### E-M2. MEDIUM — Fixture-first rule needs clarification for non-parser steps

`policy_step.md:225–231` defines a strict fixture-first rule: fixture → parser → test → mark done.

This rule is appropriate for Steps 4 and 5 (fetch and extract) but doesn't apply to Steps 1, 2, 3, 6, 7, 8 (scaffolding, domain, config, store, pipeline, CLI). The policy should scope the rule explicitly.

**Recommendation:** Add: "This rule applies to steps involving HTML/PDF parsing (Steps 4 and 5). Other steps follow the standard: write code → write test → verify → mark done."

---

## Part F — Cross-cutting Issues

### F-C1. CRITICAL — No single source of truth for `position_rows_curated` shape

This is the most impactful cross-cutting issue. Currently:
- Desiderata defines a 30+ column flat table (lines 153–210)
- Implementation says "shares `position_rows` schema" (line 238) — which is ~20 columns, missing all call-level fields
- No document defines the actual SQL for the curated view/table
- The step plan has Step 6.6 for `rebuild_curated` but doesn't define the output schema

Any session reaching Step 6.6 will have to make architectural decisions that should have been made in the plan.

**Recommendation:** Add a `### position_rows_curated` subsection to `plan_implementation.md` with the full column list. Define it as a SQL VIEW joining `calls_raw` with `position_rows` plus the employment-like WHERE clause. Include the `COALESCE(pdf_call_title, titolo) AS call_title` derivation.

### F-H1. HIGH — Commit message format inconsistency

`planning_step.md:6`: Commits should end with `(generated by Claude Code)`.
`policy_step.md:163`: Same format.
`CLAUDE.md`: Does not specify any commit message suffix.

This is a minor inconsistency but could cause confusion. Since CLAUDE.md is the authoritative AI instruction file, and commit conventions are set there for session behavior, it should mention this if it's desired.

**Recommendation:** Either add the suffix convention to CLAUDE.md or remove it from step docs if it's no longer desired.

### F-H2. HIGH — `store/export/curate.py` vs `pipeline/curate.py` — where does curation belong?

The file tree places curation logic in two layers:
- `store/export/curate.py` — SQL-level filtering
- `pipeline/curate.py` — orchestration-level wrapper

Per the layer responsibilities table (`plan_implementation.md:149`), `store/` knows "Domain objects → SQLite + CSV" and `pipeline/` knows "Orchestration order." Curation is a SQL operation (INSERT...SELECT with WHERE clause), so it belongs in `store/`. Pipeline should call it, not redefine it.

But then `pipeline/curate.py` becomes a one-line wrapper that adds no value.

**Recommendation:** Remove `pipeline/curate.py`. Have `pipeline/sync.py` call `store.export.curate.rebuild_curated(conn)` directly at the end of the sync loop. Update file tree, step plan, and CLAUDE.md accordingly. This also resolves the naming collision noted in C-C2.

### F-M1. MEDIUM — Extensibility example contradicts "new sections = new files, not edits"

`plan_implementation.md:12`: "New sections = new files, not edits."
`plan_implementation.md:268`: Extensibility example shows `store/schema.py ← only file touched: add winners table`.

Adding a table to `schema.py` is an edit, not a new file. The principle as stated is too absolute.

**Recommendation:** Reword to: "New sections primarily mean new files. Schema extensions (`store/schema.py`) and CLI registration (`cli/main.py`) are the only expected edit points."

### F-M2. MEDIUM — `pythonrequirements.txt` vs `pyproject.toml` dependency management

CLAUDE.md mentions `pythonrequirements.txt` ("used by the entrypoint to verify the venv is complete") but also specifies `pyproject.toml` with `[dev]` extras and `pip install -e ".[dev]"`.

Having two dependency sources is a maintenance burden. If `pyproject.toml` is the canonical source, `pythonrequirements.txt` should either be generated from it or removed.

**Recommendation:** Decide which is canonical. If `pyproject.toml` (preferred for modern Python), generate `pythonrequirements.txt` from it or remove the entrypoint verification that depends on it.

---

## Decisions Required Before Implementation

Ordered by impact. Each decision should result in specific edits to one or more documents.

| # | Decision | Documents affected | Severity |
|---|---|---|---|
| 1 | Define `position_rows_curated` as a SQL VIEW with full denormalized schema | `plan_implementation.md`, `planning_step.md` Step 6 | CRITICAL |
| 2 | Resolve `source_contract_type`: add as `contract_type_raw` or remove from desiderata | `plan_desiderata.md`, `plan_implementation.md`, `planning_step.md` | CRITICAL |
| 3 | Resolve `no_text` behavior: 0 rows + `pdf_fetch_status=ok`, or 1 row + `parse_confidence=low` | `plan_desiderata.md`, `plan_implementation.md` | CRITICAL |
| 4 | Choose one CLI boundary rule (relax CLAUDE.md or add pipeline/export.py wrapper) | `CLAUDE.md`, `plan_implementation.md`, `planning_step.md` | CRITICAL |
| 5 | Choose one `info_functions.md` ownership model (auto-generated only) | `policy_step.md`, `planning_step.md` | CRITICAL |
| 6 | Remove or merge `pipeline/curate.py` with `store/export/curate.py` | `plan_implementation.md`, `planning_step.md` | HIGH |
| 7 | Add 4xx handling policy to CLAUDE.md | `CLAUDE.md` | HIGH |
| 8 | Specify `dry_run` semantics | `CLAUDE.md` or `plan_implementation.md` | MEDIUM |
| 9 | Trim `planning_step.md` to summary-only (remove function signatures) | `planning_step.md` | HIGH |
| 10 | Clarify evidence grouping (per-group, not per-field) | `plan_desiderata.md` | HIGH |
| 11 | Scope fixture-first rule to parser steps only | `policy_step.md` | MEDIUM |
| 12 | Add pagination fallback procedure note | `plan_implementation.md`, `CLAUDE.md` | MEDIUM |
| 13 | Specify `detail_url` construction template | `CLAUDE.md` or `plan_implementation.md` | MEDIUM |
| 14 | Reword extensibility principle to allow schema edits | `plan_implementation.md` | MEDIUM |
| 15 | Clarify dependency direction wording | `plan_implementation.md` | HIGH |

---

## Summary

The planning documents form a solid foundation. The core architecture (layered separation, nullable-everywhere, upsert-by-detail_id, fixture-first testing) is well-designed for the problem domain.

The critical issues are:
1. **Output contract ambiguity** — `position_rows_curated` must be explicitly defined as a denormalized view.
2. **Missing field** — `source_contract_type` is in desiderata but absent from all other docs.
3. **Self-contradictory test criteria** — `no_text` behavior must be decided once.
4. **Cross-document contradictions** — CLI boundary rule and `info_functions.md` ownership need a single authoritative answer.

Once these 5 decisions are made and propagated across documents, the plan will be implementation-ready. The remaining HIGH and MEDIUM issues are important but won't block correct implementation — they're friction points that will slow sessions or produce inconsistent results.
