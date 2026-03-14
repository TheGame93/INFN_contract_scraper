## Codex Plan Author (Strict)

Default output plan file: `docs/plan_codex_parsingrefactoring.md`.

You are a planning agent. Your job is to produce a concrete implementation plan that will be executed with `docs/codex_implementing.md`.
Do not implement code in this turn unless the user explicitly asks for both planning and implementation.
The produced plan must support incremental implementation across multiple turns.

### 0) The things I want to do

For this refactoring I want the parser to become rule-driven, traceable, and modular without changing the external behavior of the sync pipeline at the boundary level. The immediate business goal is to reduce extraction errors on real INFN PDFs while we keep reviewing edge cases manually, and the engineering goal is to make parser evolution cheap so that each new edge case adds a small rule instead of adding complexity to already crowded functions. I do not want a big-bang rewrite; I want an incremental migration where the existing pipeline entrypoints remain stable and the parsing internals are progressively replaced with better-structured components.

I want the current contract between pipeline and parser to remain stable during the refactor: given extracted text, detail id, text quality, and year, the parser still returns a list of position rows and optional call-level PDF title. I want fetch, downloader, DB schema initialization, and upsert flow to remain unchanged in the first refactoring phase, so risk stays localized to parsing logic. The only behavioral change in this phase should be better parsing accuracy, better evidence quality, and deterministic reproducibility of field decisions. This keeps rollout risk low and gives us confidence as we validate against curated PDFs.

I want the parse package to be reorganized into a small number of focused subpackages with two levels of nesting maximum, so navigation remains simple. Inside `src/infn_jobs/extract/parse`, I want a `core` area that owns orchestration and lifecycle, a `rules` area that contains declarative extraction rules grouped by field and contract family, a `contracts` area that defines contract-specific profiles and overrides, a `fields` area that exposes stable adapters mapping rule outputs to the existing `PositionRow` fields, a `normalize` area for canonical conversions such as currency and subtype normalization, and a `diagnostics` area for evidence aggregation and parse decision traces. I want each file to stay short and focused, with a practical target of around 150 lines and a hard ceiling of around 250 lines; when a file reaches that limit it should be split by responsibility, not by arbitrary chunks.

I want dependency direction to be explicit and one-way. Domain models should remain at the bottom and never depend on parsing internals. Normalizers should not depend on rules. Rules should depend only on normalizers and small shared text utilities. Contract profiles should compose rules but not call storage or pipeline code. Core orchestration should call contract profiles and field adapters, then produce domain rows. Diagnostics should receive events from core and rules but should not drive extraction decisions. Pipeline should call only the parser entrypoint, as it does today. No parsing module should import anything from store or fetch.

I want parsing behavior to be phase-based and deterministic. First, text preprocessing should normalize page breaks, line endings, and whitespace in a controlled way while preserving original line references for evidence. Second, segmentation should identify candidate entry boundaries with header-aware heuristics and explicit false-split suppression. Third, segment classification should determine a contract family candidate and confidence using weighted matches instead of single-regex first-hit logic. Fourth, field extraction should run rule groups in priority order, with contract-specific overlays enabled by profile and era context. Fifth, conflict resolution should apply deterministic tie-breakers so the same input always produces the same value and same evidence selection. Sixth, final row assembly should map extracted values into current schema fields and compute parse confidence using extracted outcomes, not hidden side effects. This phased flow is what will let us reason about failures quickly.

I want rules to be data-driven in spirit even if implemented in Python objects. A rule should represent a single extraction intent and carry metadata: target field, trigger pattern, optional context guard, optional contract filter, optional era filter, value transformer, and evidence selector. I want every successful extraction to include the originating rule identifier so we can audit why a value was chosen. For now this can live in diagnostics and tests without schema change, but the internal design should support eventually persisting that trace if we decide it is useful. Rule priority should be explicit and local to each field group, and there should be a strict distinction between primary rules, fallback rules, and “do not extract here” guard rules. This prevents aggressive fallbacks from polluting results, which is exactly what happened with segmentation and generic “borsa di studio” mentions.

I want contract-specific behavior to be explicit instead of scattered. There should be a shared base profile with common extraction patterns, then thin overlays for Borsa, Incarico di ricerca, Incarico Post-Doc, Contratto di ricerca, and Assegno di ricerca. If a rule is valid for all contracts it belongs in the base profile; if it is valid for one or two contracts it belongs in those overlays only. Era logic, such as subtype validity constraints, should be centralized in profile and normalization policies, not duplicated in regex handlers. This lets fixes for one contract inherit safely where appropriate while avoiding unintended cross-contract regressions.

I want evidence handling to be strengthened because manual review is central to our workflow. The value field must always be paired with evidence chosen from the exact text region that triggered extraction, and evidence should prefer the minimal informative span rather than an overly long line when possible. For multiline patterns, evidence should preserve enough context to re-identify the clause during manual review. If multiple candidate matches exist, diagnostics should record rejected candidates and reason codes, while the stored evidence field should contain only the winning snippet. This will keep CSV and DB readable while still enabling deep debugging when needed.

I want text quality classification to be decoupled from superficial heuristics that can misclassify born-digital PDFs as OCR-clean just because a form-feed exists. The classification policy should use a small set of robust signals and should be easy to tune with fixtures. I want this policy in its own module with threshold constants and tests that cover true OCR-clean, OCR-degraded, digital, and no-text cases. We do not need a perfect classifier, but we need stable behavior and transparent reasoning because parse confidence depends on it.

I want the refactor to include a dedicated regression strategy tied to real cases we review together. Every documented edge case must have a fixture and at least one test that reproduces the previous wrong behavior and locks the expected fixed behavior. The `detail_id=4116` segmentation issue must remain as a permanent regression guard, and `detail_id=4447` should become a multi-field regression case covering subtype, income captures, evidence quality, and confidence outcome once those are agreed. Tests should be organized by phase so failures immediately point to the broken layer, and golden expectations should emphasize semantic correctness over brittle textual exactness unless evidence formatting is the target.

I want operational tooling for review velocity, because we will continue iterative PDF inspections. The parser should expose an internal review mode that, for a given detail id and local PDF path, prints structured comparison artifacts: segments found, chosen contract profile, extracted field values, evidence snippets, and rule identifiers. This is not a new product CLI yet; it is a developer support utility to accelerate our manual validation loop. The key requirement is reproducibility and compactness so we can compare “before and after” quickly for the same PDF without rerunning full sync.

I want migration to happen in vertical slices, not horizontal mega-PRs. A slice should include one field group end to end: new rules, adapter wiring, tests, and migration of existing logic from old function to new engine. During migration, legacy functions can remain as compatibility wrappers that delegate to new components until all field groups are moved, after which wrappers are removed. This keeps each change reviewable and prevents a long destabilizing branch. At every slice, existing schema and exports remain compatible unless we explicitly decide on a schema extension in a later step.

I want the definition of done for this refactor to be measurable. We should end with smaller files, no monolithic parser functions, deterministic extraction with explicit priorities, per-field evidence that is auditable, contract overlays that isolate special logic, and regression tests for all documented edge cases. We should also see concrete accuracy improvements on our reference PDFs, including the corrected position segmentation for complex Borsa bandi and improved Post-Doc financial/subtype extraction where text clearly states those values. If these outcomes are met while keeping pipeline integration stable, the refactor is successful and ready for broader edge-case expansion.

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
