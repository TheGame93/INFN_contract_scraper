# Codex Review 2.1 — Step Coherence Audit (Steps 1–5)

## Scope
Authoritative goal anchor: `docs/plan_desiderata.md`.

Review target range:
- `docs/step/implement_step1.md`
- `docs/step/implement_step2.md`
- `docs/step/implement_step3.md`
- `docs/step/implement_step4.md`
- `docs/step/implement_step5.md`

Coherence anchors used:
- `docs/plan_implementation.md`
- `CLAUDE.md`
- `docs/step/planning_step.md`
- `docs/step/policy_step.md`

## Executive Verdict
- Steps 1–5 are **partially coherent overall**.
- Step 5 has the largest coherence risk due to data-contract and acceptance-criteria contradictions.
- Cross-cutting process contradictions are already affecting this range.

## Compliance Matrix (Steps 1–5)

| Step | Status | Rationale |
|---|---|---|
| Step 1 | Partial | Structure is mostly aligned, but operates under cross-cutting tracker/policy and `info_functions` workflow conflicts (`docs/step/planning_step.md:93`, `docs/step/policy_step.md:154`, `CLAUDE.md:115`). |
| Step 2 | Partial | Domain dataclass plan follows implementation schema, but required row-level `source_contract_type` from desiderata is missing from the modeled contract (`docs/plan_desiderata.md:106`, `docs/step/implement_step2.md:95`, `docs/plan_implementation.md:210`). |
| Step 3 | Partial | Strong alignment on TIPOS verification gate, but dependent on unresolved upstream process contradictions (`docs/step/implement_step3.md:84`, `docs/step/planning_step.md:36`). |
| Step 4 | Partial | Fetch plan is mostly coherent; one branch mixes detail-fetch failure with PDF status semantics (`docs/step/implement_step4.md:281`, `docs/plan_desiderata.md:99`). |
| Step 5 | Non-compliant | Multiple contradictions: missing `source_contract_type`; `no_text` behavior conflicts with desiderata and checklist expectations (`docs/plan_desiderata.md:106`, `docs/step/planning_step.md:57`, `docs/plan_desiderata.md:246`, `docs/step/implement_step5.md:765`). |

## Findings (Critical / High / Medium)

### C2. Critical — `docs/info_functions.md` ownership workflow is contradictory
- `CLAUDE.md` says auto-generated and not hand-edited (`CLAUDE.md:115`, `CLAUDE.md:120`).
- Step policy requires manual entry updates (`docs/step/policy_step.md:154`, `docs/step/policy_step.md:241`).
- Step tracker also frames it as a manual update task (`docs/step/planning_step.md:93`).
- Impact on Steps 1–5: completion logic and session handoff are inconsistent from the beginning.
- Also impacts review 2.2 counterpart.

### C3. Critical — Required `source_contract_type` is absent from Step 1–5 execution plan
- Desiderata requires row-level extraction of `source_contract_type` (`docs/plan_desiderata.md:106`).
- Step planning for extract field modules omits this field (`docs/step/planning_step.md:57` to `docs/step/planning_step.md:63`).
- Step 2 `PositionRow` plan does not model this field (`docs/step/implement_step2.md:95` to `docs/step/implement_step2.md:120`).
- Implementation schema contract also omits it (`docs/plan_implementation.md:210` onward).
- Impact: Step 5 cannot fully satisfy stated v1 extraction goals.

### H1. High — `no_text` behavior is contradictory between desiderata and Step 5 flow
- Desiderata PDF test says `no_text` should yield zero position rows and `parse_error` (`docs/plan_desiderata.md:246`).
- Step 5 row builder guidance says still attempt extraction for `no_text` and assign low confidence rows (`docs/step/implement_step5.md:765`).
- Desiderata e2e and implementation checklist expect `no_text` rows with `parse_confidence=low` (`docs/plan_desiderata.md:269`, `docs/plan_implementation.md:285`).
- Impact: acceptance criteria are self-conflicting before Step 5 implementation starts.
- Also impacts review 2.2 counterpart.

### H2. High — Master tracker violates its own policy contract
- Policy says `planning_step.md` must be short and non-implementation-detailed (`docs/step/policy_step.md:67`).
- Actual tracker contains implementation-level signatures and command details (`docs/step/planning_step.md:39` to `docs/step/planning_step.md:94`).
- Impact on Steps 1–5: execution control-plane is overloaded; session consistency risk rises.
- Also impacts review 2.2 counterpart.

### M1. Medium — Fetch detail error branch uses PDF status field ambiguously
- Step 4 note sets `pdf_fetch_status="download_error"` on detail page fetch error (`docs/step/implement_step4.md:281`).
- Desiderata defines PDF status transitions around PDF download/parse outcomes (`docs/plan_desiderata.md:99`, `docs/plan_desiderata.md:255`).
- Impact: semantic drift between HTML-detail fetch failures and PDF-stage failures.

### M2. Medium — Fixture-first framing is only partially enforced in Step 5 narrative
- Step 5 claims fixture-first is satisfied at substep level (`docs/step/implement_step5.md:36` to `docs/step/implement_step5.md:38`).
- Policy rule is per parser/scraper/extractor workflow ordering (`docs/step/policy_step.md:225` to `docs/step/policy_step.md:231`).
- Impact: interpretation-dependent compliance, likely inconsistent behavior across sessions.

## Direct Answers (for Steps 1–5)

### Does broad planning satisfy goal in this range?
Partially. Steps 1–4 are mostly aligned; Step 5 currently misses explicit desiderata coverage (`source_contract_type`) and has conflicting `no_text` behavior.

### Does `CLAUDE.md` cover key weak spots relevant to this range?
Partially. It covers encoding/rate-limit/retry conventions, but does not resolve cross-doc workflow contradictions (`info_functions`) or acceptance mismatch around `no_text`.

### Are `plan_implementation.md` and `CLAUDE.md` coherent for Steps 1–5?
Not fully. Contract and process contradictions (especially shared cross-cutting ones) remain active in this range.

### Does `planning_step.md` comply for this range?
Partially. It captures step intent but violates policy constraints on master-tracker granularity.

### Does `policy_step.md` comply for this range?
Partially. Strong execution rigor, but inconsistent with CLAUDE on generated-doc workflow.

## Decision Blockers Before Implementation (Steps 1–5)
- Resolve `source_contract_type` contract: include or explicitly de-scope from desiderata.
- Resolve `no_text` expected behavior to one rule across desiderata/implementation/step docs.
- Unify `info_functions` workflow (generated-only vs manual updates).
- Decide whether detail-page HTTP failures should map to `pdf_fetch_status` or separate fetch-status semantics.

## Assumptions
- `docs/plan_desiderata.md` remains authoritative where conflicts exist.
- Cross-cutting issues are included here because they materially affect steps 1–5 execution quality.
- This document is review-only; no implementation/code changes are included.
