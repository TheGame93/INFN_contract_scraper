## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_6.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

Read the things to fix from `docs/plan_codex_5_codexreview.md`

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
3. First unchecked top-level step from `## Implementation Checklist` to execute next.
