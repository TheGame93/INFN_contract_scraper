## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_3.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

## Sync Modes for Partial Fetch, Incremental PDF Cache, and Local-First DB Build

The implementation should extend the existing `sync` command so that users can run the scraper in a local-first workflow while preserving compatibility with the current architecture. The codebase is already well aligned with this direction because incremental PDF caching is already implemented in the downloader and exposed through `--force-refetch`, so the main effort is to formalize source selection, phase control, and behavior on missing local inputs.

The CLI contract should be expanded with `--source local|remote|auto`, `--limit-per-tipo N`, and `--download-only`, while keeping `--dry-run` and `--force-refetch`. The default source should become `local`, and this change must be explicit in help text and logs because it alters current expectations. The debug partial fetch behavior should apply in remote mode by taking the first N calls per contract type after active and expired listings are combined in their current parsed order. This keeps behavior deterministic and easy to reason about during debugging without introducing additional sorting logic.

The pipeline should be refactored into clear internal phases: call discovery, PDF cache materialization, PDF parsing and row building, and persistence. In `download-only`, the process should stop after discovery and cache materialization so users can warm the local PDF corpus without paying parse/store costs. In `local` source mode, discovery from network should be skipped and parsing should run from cached files linked to known calls. The authoritative local input should be cached PDFs associated with existing `calls_raw` metadata, and orphan files in cache that do not map to a known `detail_id` should be skipped with warnings rather than ingested as synthetic calls. On a fresh machine where local prerequisites are absent, `sync` should fail fast with a clear actionable message instructing the user to run with `--source remote`, instead of silently falling back to network.

No mandatory schema change is required for this version, because existing fields already support the intended behavior and status tracking. Current `calls_raw` and `position_rows` structures can remain unchanged, and existing idempotency guarantees should be preserved. If provenance tracking becomes important later, an additive field can be introduced in a future iteration, but it should not block this implementation.

Validation should include parser tests for the new CLI flags and compatibility of flag combinations, orchestrator tests to confirm correct limit-per-type application semantics, and pipeline tests proving that local mode does not make network calls, download-only mode skips parse/store, cache hits avoid redundant downloads unless forced, orphan local PDFs are skipped with warnings, and local-default bootstrap failure emits clear remediation guidance. Regression coverage should explicitly confirm that remote mode still reproduces current full-sync idempotent behavior.

```bash
python3 -m infn_jobs --help
python3 -m infn_jobs sync                                  # default local mode: parse/store from local cache + existing DB metadata
python3 -m infn_jobs sync --source remote                  # full remote sync: fetch + download + parse + write to DB
python3 -m infn_jobs sync --source remote --dry-run        # fetch + parse only, no DB writes
python3 -m infn_jobs sync --source remote --force-refetch  # full remote sync and re-download PDFs even if cached
python3 -m infn_jobs sync --source remote --limit-per-tipo 20   # debug partial fetch: first 20 calls per tipo
python3 -m infn_jobs sync --source remote --download-only        # fetch calls + download/cache PDFs only (no parse/store)
python3 -m infn_jobs sync --source remote --download-only --limit-per-tipo 20  # debug cache warm-up
python3 -m infn_jobs sync --source local --dry-run         # parse local cached PDFs only, no DB writes
python3 -m infn_jobs sync --source auto                    # hybrid mode (local-first behavior, remote when needed)
python3 -m infn_jobs export-csv                            # rebuild curated data and write the 4 CSV files
```

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
3. First unchecked top-level step from `## Implementation Checklist` to execute next.
