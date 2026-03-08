# Codex Review 2.2 — Step Coherence Audit (Steps 6–9)

## Scope
Authoritative goal anchor: `docs/plan_desiderata.md`.

Review target range:
- `docs/step/implement_step6.md`
- `docs/step/implement_step7.md`
- `docs/step/implement_step8.md`
- `docs/step/implement_step9.md`

Coherence anchors used:
- `docs/plan_implementation.md`
- `CLAUDE.md`
- `docs/step/planning_step.md`
- `docs/step/policy_step.md`

## Executive Verdict
- Steps 6–9 are **partially coherent overall**.
- Step 8 is non-compliant due to CLI boundary conflict.
- Step 6 and Step 9 embed unresolved contract contradictions from upstream docs.

## Compliance Matrix (Steps 6–9)

| Step | Status | Rationale |
|---|---|---|
| Step 6 | Non-compliant | Curated schema contract conflicts with desiderata output expectations; internal contradiction on empty-row upsert semantics (`docs/plan_desiderata.md:153`, `docs/plan_implementation.md:238`, `docs/step/implement_step6.md:133`, `docs/step/implement_step6.md:135`). |
| Step 7 | Partial | Pipeline orchestration is mostly explicit, but inherits unresolved `no_text` contract and rate-limit assumptions (`docs/step/implement_step7.md:99`, `docs/step/implement_step7.md:114`, `docs/plan_desiderata.md:246`). |
| Step 8 | Non-compliant | CLI contract violates `cli -> pipeline only` rule by calling store export directly (`CLAUDE.md:60`, `docs/step/implement_step8.md:153`, `docs/plan_implementation.md:168`). |
| Step 9 | Partial | E2E/generation flow is strong, but still carries `no_text` contradiction and cross-doc `info_functions` process conflict (`docs/step/implement_step9.md:103`, `docs/step/implement_step9.md:8`, `docs/step/policy_step.md:154`). |

## Findings (Critical / High / Medium)

### C1. Critical — CLI boundary contradiction remains unresolved in execution steps
- CLAUDE rule: `cli` only calls `pipeline` (`CLAUDE.md:60`).
- Step 8 export command explicitly calls store export layer (`docs/step/implement_step8.md:153`, `docs/step/implement_step8.md:160`).
- Implementation plan still documents direct `cmd_export -> store.export` behavior (`docs/plan_implementation.md:27`, `docs/plan_implementation.md:168`).
- Impact: architecture contract is not decision-complete; Step 8 can be implemented two different ways.
- Also impacts review 2.1 counterpart.

### C2. Critical — `docs/info_functions.md` process conflict persists into completion phase
- Step 9 correctly treats `info_functions` as generated (`docs/step/implement_step9.md:8`, `docs/step/implement_step9.md:126`).
- Policy still requires manual updates (`docs/step/policy_step.md:154`, `docs/step/policy_step.md:241`).
- Tracker wording still reads as manual update task (`docs/step/planning_step.md:93`).
- Impact: project-close workflow is contradictory at Step 9.
- Also impacts review 2.1 counterpart.

### C4. Critical — Curated row contract mismatch remains in store/export steps
- Desiderata canonical `position_rows_curated` includes call-level and status fields (`docs/plan_desiderata.md:153` to `docs/plan_desiderata.md:175`).
- Implementation/store plan keeps curated schema identical to raw row schema (`docs/plan_implementation.md:238`, `docs/step/implement_step6.md:36`).
- Step 6 export writes `SELECT *` for position rows, preserving that narrower schema (`docs/step/implement_step6.md:229`).
- Impact: analytical output contract remains underspecified/inconsistent.

### H1. High — `no_text` acceptance contradictions are still present in late steps
- Desiderata says `no_text` => `0 position_rows`, `parse_error` (`docs/plan_desiderata.md:246`).
- Step 7 success path can produce `pdf_fetch_status="ok"` after build flow (`docs/step/implement_step7.md:99`).
- Step 9 verification expects degraded/no_text rows with low confidence (`docs/step/implement_step9.md:103`).
- Impact: Step 7/9 verification may pass under behavior that conflicts with desiderata tests.
- Also impacts review 2.1 counterpart.

### H2. High — Master tracker/policy mismatch still impacts completion governance
- Policy requires summary-only master tracker (`docs/step/policy_step.md:67`).
- Tracker remains implementation-detailed (`docs/step/planning_step.md:65` to `docs/step/planning_step.md:94`).
- Impact: final status marking in Step 9 is tied to a tracker format that violates policy.
- Also impacts review 2.1 counterpart.

### H3. High — Step 6 has internal contradiction on empty-list row replacement semantics
- Step 6.4 test command name implies empty-list should clear rows (`docs/step/implement_step6.md:133`).
- Step 6.4 notes say empty list is noop and return (`docs/step/implement_step6.md:135`).
- Step 6.5 test list also uses noop semantics (`docs/step/implement_step6.md:160`).
- Impact: upsert behavior is not decision-complete for edge case handling.

### M1. Medium — PDF download rate-limit responsibility is ambiguous across step docs
- Desiderata requires sleep between every request including PDF download (`docs/plan_desiderata.md:62`).
- Step 7 states rate limiting is enforced inside `download` (`docs/step/implement_step7.md:114`).
- Step 5 downloader notes do not specify rate-limit sleep behavior (`docs/step/implement_step5.md:54` to `docs/step/implement_step5.md:60`).
- Impact: request pacing may diverge depending on implementer interpretation.

## Direct Answers (for Steps 6–9)

### Does broad planning satisfy goal in this range?
Partially. Core flow is represented, but CLI boundary, curated output contract, and edge semantics are not fully coherent.

### Does `CLAUDE.md` cover key weak spots relevant to this range?
Partially. It provides useful runtime conventions, but does not resolve contradictions with implementation/step docs.

### Are `plan_implementation.md` and `CLAUDE.md` coherent for Steps 6–9?
No. The CLI/export boundary contradiction is explicit and directly impacts Step 8.

### Does `planning_step.md` comply for this range?
Partially. It tracks all required steps but remains out of policy format.

### Does `policy_step.md` comply for this range?
Partially. Strong procedural controls, but contradicts generated-doc behavior that Step 9 follows.

## Decision Blockers Before Implementation (Steps 6–9)
- Decide and enforce one CLI boundary model for export path.
- Decide final curated-row output contract (`position_rows_curated` schema vs denormalized export contract).
- Resolve empty-list behavior for `upsert_position_rows` and align tests/notes.
- Resolve `no_text` handling end-to-end (status + row presence + confidence expectations).
- Resolve ownership model for `docs/info_functions.md` in policy/tracker.

## Assumptions
- `docs/plan_desiderata.md` remains authoritative for requirement intent.
- Cross-cutting findings are duplicated only when they materially affect Steps 6–9.
- This document is review-only; no implementation/code changes are included.
