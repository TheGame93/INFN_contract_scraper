## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_parsefixing.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

Understood, from this point we will communicate in English.

The parser specification needs to be updated so that contract subtype and income extraction are aligned with real contract language, especially in OCR-clean but line-broken PDFs like `4490.pdf`. The intended behavior is that `Contratto di ricerca`, `Incarico di ricerca`, and `Incarico post-doc` support subtype extraction for both Roman and Arabic forms of fascia levels, meaning `Fascia I/II/III` and `Fascia 1/2/3`, while preserving canonical normalization and storing the original snippet in the raw field. For `Assegno di ricerca`, subtype semantics must be aligned to `junior` and `senior`, with deterministic canonical values and raw evidence retained exactly as found. This is a behavior-level requirement and should be treated as a source-of-truth update, not just a test patch.

The income rules must expand institute-cost recognition beyond current narrow labels so that wording equivalent to “oneri a carico dell’istituto” and “importo annuo complessivo … comprensivo di oneri a carico dell’Istituto” is recognized as institute cost total when monetary context is present. Gross yearly income must continue to map to annual gross compensation wording such as “compenso lordo annuo omnicomprensivo”. The desired end state for `detail_id=4490` is explicit extraction of subtype `Fascia 1`, `institute_cost_total_eur = 27.819,00`, and `gross_income_yearly_eur = 22.500,00`, each with correct evidence text.

A cross-cutting refactor is required for newline robustness across parser fields, not only for income. The current single-line label/value assumption must be replaced by a shared parse-layer strategy that can evaluate adjacent lines as a logical unit while keeping deterministic behavior and evidence traceability. This capability is expected to be reusable by contract identity, income, duration, and other rule-driven fields where labels and values are frequently split across lines in INFN templates. The architecture should keep responsibilities in the parse layer and avoid duplicated ad hoc fixes inside each rule module.

The expected repository touch points are the contract profile and subtype normalization logic under `src/infn_jobs/extract/parse/contracts` and `src/infn_jobs/extract/parse/normalize`, contract-identity rule modules under `src/infn_jobs/extract/parse/rules`, income helper/spec modules under the same rules package, and any shared helper introduced for multiline matching inside parse core/rules utilities. The runtime contracts must remain unchanged for `build_rows`, `run_parse_pipeline`, and persistence schema. Outputs remain nullable where evidence is absent, and rule execution must stay deterministic with stable precedence semantics.

Testing and regression expectations are that canary coverage remains green and is strengthened with assertions for the new 4490 values, plus focused tests for multiline label-value extraction and subtype variants across affected contract families. The provenance and canary integrity checks must still pass. Since behavior changes are intentional, documentation must be synchronized in `docs/plan_desiderata.md`, `docs/plan_implementation.md`, and `CLAUDE.md`, and `docs/info_functions.md` must be regenerated if public signatures change. CSV structure is not expected to change, so `docs/info_csvfields.md` should only be updated if field definitions or exported columns actually change.

The planner must account for false-positive risk from broad financial wording, OCR artifacts around Roman numerals (`I` vs `1`), and cross-line numeric parsing that could accidentally capture unrelated numbers. The target architecture should minimize these risks through context-aware matching, deterministic conflict resolution, and explicit evidence anchoring, while respecting project conventions on layer boundaries, idempotency, null-safety, and parser module maintainability limits.

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
