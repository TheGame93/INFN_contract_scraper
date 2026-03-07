# Codex Review 1 — Top-Down Planning Coherence Audit (Revision 2)

## Scope
Authoritative goal document for this audit: `docs/plan_desiderata.md`.

Reviewed documents:
- `docs/plan_implementation.md`
- `CLAUDE.md`
- `docs/step/planning_step.md`
- `docs/step/policy_step.md`

## Executive Verdict
- `plan_implementation` vs `plan_desiderata`: **Partially compliant** (with critical gaps).
- `CLAUDE.md` weak-spot coverage of `plan_implementation`: **Good but incomplete**.
- `plan_implementation.md` and `CLAUDE.md` coherence: **Not coherent**.
- `planning_step.md` compliance vs desiderata/implementation/CLAUDE (+policy constraints): **Partially compliant**.
- `policy_step.md` compliance vs desiderata/implementation/CLAUDE: **Partially compliant**.

## Findings (Ordered by Severity)

### C1. Critical — CLI boundary conflict between architecture docs
- `CLAUDE.md` mandates: `cli` only calls `pipeline` (`CLAUDE.md:60`).
- `plan_implementation.md` defines `cmd_export.py` calling `store.export` directly (`docs/plan_implementation.md:27`, `docs/plan_implementation.md:168`).
- `planning_step.md` repeats direct `cli -> store` for export (`docs/step/planning_step.md:87`).
- Impact: sessions can implement two different architectures.

### C2. Critical — `docs/info_functions.md` workflow is contradictory
- `CLAUDE.md`: auto-generated, do not edit by hand (`CLAUDE.md:115`, `CLAUDE.md:117` to `CLAUDE.md:121`).
- `policy_step.md`: manually add/verify entries in checklists (`docs/step/policy_step.md:154`, `docs/step/policy_step.md:179`, `docs/step/policy_step.md:241`).
- `planning_step.md`: asks to update it as a manual step (`docs/step/planning_step.md:93`).
- Impact: deterministic process cannot be followed consistently.

### C3. Critical — Required `source_contract_type` is absent from implementation and step plan
- Desiderata requires row-level extraction of `source_contract_type` (`docs/plan_desiderata.md:106`).
- `plan_implementation.md` data model and schema do not include it (`docs/plan_implementation.md:210` onward).
- `planning_step.md` extractor tasks do not include this field (`docs/step/planning_step.md:57` to `docs/step/planning_step.md:61`).
- Impact: stated goal cannot be fully met as documented.

### C4. Critical — `position_rows_curated` contract mismatch
- Desiderata canonical output for `position_rows_curated` includes call-level metadata and status fields (`docs/plan_desiderata.md:153` to `docs/plan_desiderata.md:175`).
- Implementation says `position_rows_curated` shares `position_rows` schema (`docs/plan_implementation.md:238`), which omits those call-level fields unless joined externally.
- Impact: analytics contract is underspecified and likely inconsistent across DB/CSV expectations.

### H1. High — Internal contradiction on `no_text` behavior
- Desiderata test says `no_text` should yield 0 rows (`docs/plan_desiderata.md:246`).
- Desiderata e2e check expects `no_text` rows with `parse_confidence = low` (`docs/plan_desiderata.md:269`).
- Implementation checklist repeats the latter (`docs/plan_implementation.md:285`).
- Impact: acceptance criteria are self-conflicting.

### H2. High — `planning_step.md` violates `policy_step.md` scope rules
- Policy requires the master tracker to remain short and summary-only (`docs/step/policy_step.md:30`, `docs/step/policy_step.md:67`).
- `planning_step.md` includes implementation-level details, function signatures, and command specifics (`docs/step/planning_step.md:39` to `docs/step/planning_step.md:94`).
- Impact: the master tracker is no longer a lightweight control plane.

### H3. High — Dependency model is internally ambiguous
- `plan_implementation.md` says dependency direction is `domain <- pipeline <- cli` (`docs/plan_implementation.md:11`), while also saying infrastructure layers implement domain interfaces.
- `CLAUDE.md` states a different practical rule set (`CLAUDE.md:58` to `CLAUDE.md:60`).
- Impact: architectural boundaries are unclear even before coding starts.

### H4. High — Extensibility principle contradicts its own example
- Principle: add new sections via new files, not edits (`docs/plan_implementation.md:12`).
- Example still requires editing `store/schema.py` (`docs/plan_implementation.md:268`).
- Impact: “no edits” rule is not actually enforceable as written.

### H5. High — Evidence granularity likely below desiderata requirement
- Desiderata asks for evidence snippet for every parsed field (`docs/plan_desiderata.md:122`, `docs/plan_desiderata.md:208`).
- Schema defines grouped evidence fields (`institute_cost_evidence`, `gross_income_evidence`, `net_income_evidence`) rather than per numeric field (`docs/plan_implementation.md:228` to `docs/plan_implementation.md:230`).
- Impact: auditability requirement may be only partially satisfied.

### M1. Medium — CLAUDE misses key operational guardrails from desiderata
- Missing explicit pagination fallback procedure (`docs/plan_desiderata.md:67`).
- Missing explicit gate to verify `TIPOS` before Step 4 (`docs/plan_desiderata.md:69`, `docs/step/planning_step.md:36`).
- Missing explicit 4xx handling policy mapping in conventions (`docs/plan_desiderata.md:63`).
- Impact: recurring failure modes are less constrained for future sessions.

### M2. Medium — `planning_step` active-pointer granularity is inconsistent with its own index
- `Currently Active` points to `1.1.1` (`docs/step/planning_step.md:12`).
- The same file index only tracks `1.1`, `1.2`, ... and not per-sub-substep status (`docs/step/planning_step.md:20` onward).
- Impact: progress state is split across files and harder to keep atomic.

### M3. Medium — Policy sub-substep definition conflicts with actual step execution style
- Policy defines sub-substep as one file/function unit (`docs/step/policy_step.md:43`).
- Existing step docs include shell-verification sub-substeps with no file/function write (e.g., `docs/step/implement_step1.md:55` to `docs/step/implement_step1.md:60`).
- Impact: policy language does not fully describe real workflow.

### M4. Medium — Session-reading guidance has mild tension
- `CLAUDE.md`: always read relevant subsystem doc before work (`CLAUDE.md:34`).
- `policy_step.md`: do not re-read desiderata/implementation unless unclear (`docs/step/policy_step.md:130`).
- Impact: not a hard contradiction, but it can produce inconsistent review depth across sessions.

## New Findings Added In This Revision
Compared to the previous draft, this revision adds or sharpens:
- H3 dependency-model ambiguity.
- H4 extensibility principle self-contradiction.
- H5 evidence granularity mismatch risk.
- M2 active-pointer/index granularity issue.
- M3 policy definition vs real sub-substep shape.
- M4 session-reading guidance tension.

## Direct Answers To Your Questions

### 1) Does `plan_implementation` satisfy `plan_desiderata`?
Partially. It captures the overall architecture, but misses critical required contracts (`source_contract_type`) and has unresolved output-schema ambiguity (`position_rows_curated`).

### 2) Does `CLAUDE.md` address all key weak spots of `plan_implementation.md`?
No. It covers several major weak spots well (encoding, retries, rate limiting, PDF URL resolution, parse-confidence semantics), but not all operational constraints from desiderata (pagination fallback, tipo verification gate, explicit 4xx mapping).

### 3) Are `plan_implementation.md` and `CLAUDE.md` coherent?
Not fully. There are direct contradictions (CLI boundary) and architectural ambiguities (dependency wording).

### 4) Does `planning_step.md` comply with desiderata/implementation/CLAUDE?
Partially. It tracks many required activities but inherits major architecture/process conflicts and violates policy rules for what belongs in the master tracker.

### 5) Does `policy_step.md` comply with desiderata/implementation/CLAUDE?
Partially. It is strong on execution discipline but conflicts with CLAUDE on function-index ownership and does not fully match current step-document reality.

## Decisions To Resolve Before Implementation
- Choose one CLI boundary rule and apply it across all docs.
- Choose one `docs/info_functions.md` ownership model (auto-generated vs manual).
- Decide whether `position_rows_curated` is normalized-only or denormalized analytical output.
- Decide whether `source_contract_type` is mandatory in v1 stored/exported schema.
- Resolve `no_text` acceptance criteria to one consistent behavior.

## Assumptions
- `docs/plan_desiderata.md` remains authoritative in conflicts.
- This is a documentation review only; no implementation changes were made.
