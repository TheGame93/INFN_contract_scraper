## Codex Plan Author (Strict)

Default output plan file: `docs/plan_claude_sourcefix.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

The sync pipeline currently uses the SQLite database as the source of truth for --source local discovery: it reads all rows from calls_raw, attempts to match each to a cached PDF, and upserts all of them regardless of whether a PDF was found. This means the database can contain thousands of entries even when only a handful of PDFs are actually present in the cache directory. The user wants a fundamentally different invariant: after any sync run, the database must contain exactly and only the contracts whose PDFs physically exist in data/pdf_cache/. The cache directory becomes the source of truth, not the database.

The --source local mode should be reimplemented so that Phase A discovery works by scanning the filesystem — globbing data/pdf_cache/*.pdf — and deriving the set of contracts to process from the filenames alone. Each PDF filename encodes a detail_id as its stem. For each discovered file, the pipeline should attempt to load the existing CallRaw metadata from the database to preserve previously fetched fields like anno, titolo, source_tipo, numero_posti_html, and so on. If no database record exists for a given detail_id, the pipeline must still proceed with a minimal CallRaw carrying only detail_id and pdf_cache_path, because all fields are nullable by design and the parser must tolerate missing metadata.

The --source remote mode should be reimplemented as a superset of local: it starts with the same filesystem scan of data/pdf_cache/, then additionally fetches from the website to discover new contracts not yet present in the cache. Any newly discovered contracts have their PDFs downloaded into pdf_cache/. The final set processed is the union of what was already cached and what was freshly downloaded. Both modes therefore share the same invariant about the database reflecting the cache, and both must run the same prune step at the end of Phase D.

The prune step is the second major new element. After all upserts are complete in Phase D, the pipeline must delete from calls_raw and position_rows any rows whose detail_id is not in the set of contracts that were processed in the current sync run. This must happen inside _persist_sync_results after the curated rebuild. The prune must have a safety guard: if the active set is empty (for example because the cache directory is empty), the prune must be skipped entirely to avoid accidentally wiping the entire database. When pruning does occur, the count of deleted calls_raw rows should be logged at INFO level via runtime_logger.

The --source auto mode must be removed entirely. The CLI argument parser must no longer accept auto as a valid choice, and the dispatch logic inside _discover_calls must raise a clear error if auto is somehow passed. All references to auto in tests, documentation, and the CLAUDE.md conventions section must be removed or updated.

The orphan cache file warning function _warn_orphan_cache_files becomes meaningless under the new semantics — since all PDFs in pdf_cache/ are by definition processed, no file in that directory can be orphaned. This function and its call site should be removed.

Regarding responsibilities: the store layer must gain two new functions. One is a reader that loads a single CallRaw by detail_id from the database, returning None if not found; this belongs in store/read.py alongside the existing list_calls_for_pdf_processing. The other is a pruning function that accepts the set of active detail_id strings and deletes all database rows not in that set from both calls_raw and position_rows; this belongs in store/upsert.py. The pipeline layer (pipeline/sync.py) orchestrates discovery and calls these store functions; it must not contain raw SQL. The CLI layer only changes to remove auto from argument choices.

The existing constraints from the project conventions must be respected throughout. All fields remain nullable. The upsert_call function preserves first_seen_at on update. upsert_position_rows continues its delete-then-insert behavior per detail_id. The rebuild_curated call happens before the prune so the curated tables are also cleaned up. The --dry-run flag must suppress all writes including the prune step. The --download-only and --force-refetch flags remain invalid with --source local. The --limit-per-tipo flag continues to apply only to the remote discovery portion of --source remote.

The key risk the planner must account for is the empty-cache safety guard on prune: running --source local with an empty cache directory should be a no-op on the database, not a destructive wipe. The planner must also account for the case where --source remote discovers remote contracts already present in the cache — those should not be double-processed; the merge of local and remote sets must be deduplicated by detail_id. The planner should also note that tests covering --source local behavior will need substantial updates since the current tests mock fetch_all_calls and rely on DB-driven discovery, which no longer applies. New tests are needed to cover filesystem-driven discovery, metadata loading from DB, minimal CallRaw fallback, and the prune behavior.

### 1) Mandatory reads (at start of turn)
1. Read `CLAUDE.md`.
2. Read `docs/plan_desiderata.md`.
3. Read `docs/plan_implementation.md`.
4. Read `docs/info_functions.md` (if present).
5. Read `docs/step/policy_step.md` and `docs/step/planning_step.md` (if present).
6. Read all user-provided inputs for planning (audit/spec/issues)
7. Read relevant source files/tests to truth-check what is already implemented.

### 2) Planning objective
1. Convert findings/requirements into deterministic steps that can be executed incrementally.
2. Optimize ordering for safety and delivery:
   - reliability/crash/data-integrity fixes first,
   - missing behavior/tests second,
   - investigation-only items before risky parser refactors,
   - low-priority cleanup/docs last.
3. Keep scope minimal and explicit for each step.
4. Ensure each planned action is traceable to a source requirement/finding ID.
5. Make incremental execution state explicit, so implementation can resume from the correct step.

### 3) Truth-check before writing the plan
1. For every requirement/finding, verify current code/tests and classify:
   - already satisfied,
   - missing,
   - partially covered,
   - unclear/theoretical risk requiring evidence.
2. Identify conflicts or constraints from `CLAUDE.md` and architecture docs.
3. Identify likely implementation risks early (dependency conflicts, brittle tests, hidden coupling, fixture gaps).
4. Add explicit mitigations inside the plan for those risks.

### 4) Plan design rules (mandatory)
1. Use top-level steps and numbered substeps (`Step N`, `N.x`).
2. Every top-level step must be independently actionable and verifiable.
3. Every substep must specify:
   - target files to edit/create,
   - expected behavior change,
   - tests to add/update,
   - focused verification commands.
4. Include investigation decision gates when evidence is required before changing behavior.
5. Avoid vague instructions ("improve parser", "refactor broadly"). Be file- and behavior-specific.
6. Preserve architecture boundaries (`domain`, `fetch`, `extract`, `store`, `pipeline`, `cli`) and idempotency rules.
7. Do not include speculative features unless the user explicitly asked for them.

### 5) Test and verification planning
1. Map each behavior change to at least one test target.
2. Include focused verification per step/substep, then full mandatory verification at the end:
   - `pytest tests/ -v`
   - `ruff check src/`
3. If an item is documentation/policy-only, still include a consistency check.
4. If something cannot be validated yet, state what evidence is missing and how to collect it.

### 6) Documentation sync rules
If planned work changes behavior, fields, schema, file structure, or public function signatures, include explicit doc-update tasks for:
1. `docs/plan_desiderata.md`
2. `docs/plan_implementation.md`
3. `CLAUDE.md`
4. `docs/info_functions.md` via `python3 scripts/gen_info_functions.py` (when functions/classes are added, renamed, removed)
5. `docs/info_csvfields.md` when exported CSV structure changes (add/remove rows for changed fields)

### 7) Output format (must follow)
Write/update the target plan file in Markdown with this structure:

1. `# <Plan title>`
2. `## Inputs and truth references`
   - list exact files used as source of truth.
3. `## Execution order`
   - concise numbered order with rationale.
4. `## Implementation Checklist`
   - add one checkbox per top-level step, all initialized as unchecked:
   - `- [ ] Step 1 — ...`
   - `- [ ] Step 2 — ...`
   - This checklist is mandatory and is the source of truth for incremental progress.
5. `## Step 1 — ...`
   - `### 1.0 Pre-check findings and mitigations` (if relevant)
   - `### 1.1 ...`, `### 1.2 ...` etc with concrete file/test targets.
   - `### 1.x Validate Step 1`
6. Repeat for all planned steps.
7. `## Deliverables Checklist (By Finding/Requirement ID)`
   - one line per ID: fixed / investigate-first / deferred-with-rationale.
8. `## Final Verification`
   - include `pytest tests/ -v` and `ruff check src/`.

### 8) Quality gate before finalizing the plan
1. Check that every input finding/requirement ID appears in the checklist.
2. Check that every top-level step appears in `## Implementation Checklist` as an unchecked item (`[ ]`).
3. Check that each step has concrete files and tests (not generic prose only).
4. Check that step order is dependency-safe and minimizes rollback risk.
5. Check that the plan is executable by `docs/codex_instructions.md` one top-level step at a time.
6. Remove duplicates and merge overlapping tasks.

### 9) Response rule
After writing the file, respond with:
1. Plan file path.
2. What changed (high level).
3. All the planned steps: (Step # - name - oneline description - suggest the current AI reasoning depth for that step)
