## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_numberresilience.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

The planner should define a refactor that makes position row cardinality consistent with reliable listing metadata, because current behavior can produce extra preamble rows that look like real contracts and create misleading NULL values in audits. The core problem is not only line-break sensitivity in regex matching, but also that every parsed segment is currently persisted as a position_row, which allows boilerplate segments to survive as row 0 when numero_posti_html indicates a single position. The desired end state is that persisted position_rows represent contract-bearing rows only, with deterministic behavior and explicit observability when reconciliation decisions are made.

The architecture should keep parsing responsibilities in the extract/parse area and orchestration decisions in the pipeline layer. Segment parsing should still produce raw candidate rows from PDF text, but persistence-time reconciliation should use call-level context from calls_raw, especially numero_posti_html, to decide whether parsed rows are structurally plausible. The planner should preserve separation of concerns by introducing a dedicated reconciliation component, rather than embedding ad hoc filters directly inside unrelated functions. That component should accept parsed rows plus relevant call metadata, return the rows to persist, and emit deterministic reasons for any dropped rows so diagnostics and logs remain explainable.

Behaviorally, when numero_posti_html is exactly one and parsing yields multiple rows, the system should keep the strongest contract row and drop weaker boilerplate rows. Strength should be derived from existing parsed signals already present on PositionRow, such as subtype, duration, income fields, and high-quality section evidence, with deterministic tie-breaking so repeated runs are identical. The planner must not enforce the inverse relation, because one contract row for multiple posted positions is valid. When numero_posti_html is missing, invalid, or inconsistent with historical anomalies, the system should degrade gracefully and avoid destructive trimming unless confidence in the reconciliation decision is high. The reconciliation should never crash sync and should align with the project rule that fields are nullable and partial runs are safe.

The expected repository touch points are the sync orchestration path where build_rows output is currently persisted, the parse core area for any shared row-strength evaluation helper if needed, diagnostics and logging surfaces so row drops are visible, and tests across pipeline and parser-adjacent behavior. Store schema and spec files should remain unchanged unless the planner explicitly chooses to persist reconciliation diagnostics, in which case spec-driven schema conventions must be followed. Existing newline hardening in shared text-window utilities should be treated as complementary robustness work, not the primary fix for row overproduction.

Inputs that matter are PDF-derived parsed rows, detail_id, position_row_index, and numero_posti_html from CallRaw. Outputs are the reconciled list of rows passed to upsert_position_rows and runtime log events describing any reconciliation action. Side effects include potential changes in row counts per detail and changed position_row_index sequences after filtering, so idempotency and deterministic ordering must be preserved. If rows are filtered, indices should still be deterministic and stable for identical inputs, with explicit policy on whether indices are compacted or original segment indices are preserved, because future FK expectations around (detail_id, position_row_index) are already documented.

Constraints from repository conventions must be respected: docstrings on public functions, one concern per file, deterministic behavior, no domain-layer I/O, and pipeline as the wiring layer. The planner must preserve parse review/runtime parity principles and ensure any new logic does not silently diverge between normal parsing and review tooling where that would impair debugging. Test coverage should explicitly include cases like 4441 and 4458, cases with true multiple contracts, cases with one contract and many positions, and cases with missing numero_posti_html. The planner should also account for older noisy templates and OCR variability so reconciliation improves quality without discarding legitimate rows.

The canary set must now include detail_id 4441 and 4458 in addition to the existing canaries, and all audit/provenance/comparison steps must be applied to these two contracts as well.

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
3. All the planned steps: (Step # - name - oneline description - suggest the CODEX reasoning depth for that step)
