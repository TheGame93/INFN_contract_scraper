## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_terminaloutput.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

This change is a logging and runtime-observability refactor for the sync command, motivated by the fact that terminal output is currently too verbose and likely contributes to perceived slowness, especially in local mode when processing roughly 4300 PDFs. The desired end state is that detailed operational logs are still fully captured, but they are written to a logfile rather than streamed to the terminal, while terminal output is intentionally minimal and performance-focused for all source modes, including local, remote, and auto.

The behavior target is that sync runs print only concise runtime progress information on stdout and never emit per-contract INFO spam. The terminal should show a compact start message, lightweight periodic heartbeat updates at a stable interval suitable for large workloads, phase-level elapsed times for the major sync phases, and one final summary that reports total processed contracts and total runtime, with enough counters to understand outcomes without opening the logfile. Warnings and errors must remain visible on the terminal. All detailed INFO diagnostics that currently help debugging and audits must remain available, but in a per-run logfile stored under a runtime artifacts location inside data, with deterministic naming that makes runs easy to find later.

The repository areas expected to be touched are the CLI logging configuration, sync pipeline progress emission, runtime directory setup, documentation, and tests that currently depend on log behavior. The architectural intent is to keep responsibility boundaries intact: CLI owns global logging configuration, pipeline owns orchestration and high-level progress reporting, and lower layers keep using module loggers without printing directly. No data extraction, parsing, schema, or store logic should be changed as part of this refactor. The sync contracts and semantics for source selection, dry-run, and download-only must remain exactly the same, with only observability behavior changed.

Inputs and outputs that matter are command-line sync invocations across all source modes and their existing flags, terminal lines shown during execution, and logfile content written during execution. Side effects include creating a logs directory if needed and writing one logfile per run; this location should be treated as runtime artifact output and excluded from version control the same way other generated data is excluded. The final terminal summary must remain meaningful whether the run completes normally, exits early due to dry-run or download-only, or is interrupted. The planner should account for how processed-contract counting is defined so summaries stay consistent across modes and early exits.

Constraints from project conventions must be respected. Logging in library modules must remain logger-based with no print calls outside CLI user interaction paths. Dependency direction and layer ownership must not be violated. Existing null-safety and idempotent sync guarantees are unaffected and must stay untouched. Changes should remain minimal in scope and avoid unrelated refactors. Public behavior expectations documented in README and internal docs should be updated so users understand where verbose logs go and what terminal output to expect. If any public function or class signatures change, the auto-generated function index must be regenerated according to project rules.

Risks and edge cases the planner must explicitly cover include maintaining parity of behavior across local, remote, and auto despite different discovery and cache flows, avoiding regressions in tests that currently assert specific log messages, ensuring warnings and pressure-signal guidance remain visible to users even when INFO is redirected to file, preventing accidental logfile churn in git, handling empty or very small runs without noisy output, handling interruption paths so final runtime messaging remains coherent, and ensuring that reduced terminal output does not remove critical operational visibility needed for long runs near the 4300-PDF workload size.

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
