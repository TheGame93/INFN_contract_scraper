# Plan Codex 6 — Hardening `upsert_position_rows` Input Contract

## Inputs and truth references
- `docs/plan_codex_5_codexreview.md` (source findings to address)
- `CLAUDE.md`
- `docs/plan_desiderata.md`
- `docs/plan_implementation.md`
- `docs/info_functions.md`
- `docs/step/policy_step.md`
- `docs/step/planning_step.md`
- `src/infn_jobs/store/upsert.py`
- `src/infn_jobs/pipeline/sync.py`
- `tests/store/test_upsert.py`
- `tests/e2e/test_sync.py`

## Execution order
1. Confirm real call-path assumptions and lock the failure surface first, so behavior tightening does not introduce hidden regressions.
2. Enforce a deterministic input contract in `upsert_position_rows` and add explicit regression tests.
3. Run full verification and close with documentation consistency checks only where behavior/contracts changed.

## Implementation Checklist
- [x] Step 1 — Baseline and decision gate for `upsert_position_rows` batch contract
- [ ] Step 2 — Enforce homogeneous `detail_id` contract and add regression tests
- [ ] Step 3 — Verification closure and contract documentation sync

## Step 1 — Baseline and decision gate for `upsert_position_rows` batch contract
### 1.0 Pre-check findings and mitigations
- Findings in scope: `Medium-01`.
- Current classification:
  - `Medium-01` heterogeneous `detail_id` batch handling is **partially covered**: current pipeline path builds homogeneous rows per call, but helper-level contract is not enforced.
- Risks:
  - Contract tightening can break unknown callers if they currently pass mixed batches.
  - Silent data inconsistencies remain possible if helper reuse expands beyond current pipeline flow.
- Mitigations:
  - Inventory all call sites before behavior changes.
  - Keep changes minimal and local to `store/upsert.py` + dedicated tests.
  - Validate existing pipeline/e2e flows after test updates.

### 1.1 Inventory call-sites and characterize existing behavior
- Target files to edit/create:
  - `src/infn_jobs/store/upsert.py` (read-only during this substep)
  - `src/infn_jobs/pipeline/sync.py` (read-only during this substep)
  - `tests/store/test_upsert.py` (read-only during this substep)
- Expected behavior change:
  - None (investigation-only gate).
- Tests to add/update:
  - None in this substep.
- Focused verification commands:
  - `rg -n "upsert_position_rows\\(" src/ tests/`
  - `pytest tests/store/test_upsert.py -k position_rows -v`

### 1.2 Investigation evidence snapshot (this step)
- Evidence collected:
  - Production pipeline call path (`pipeline/sync.py`) calls `upsert_position_rows(conn, item.rows)` where `item.rows` are produced by `build_rows(text, detail_id, ...)` per-call, so rows are homogeneous in the current runtime flow.
  - Test call-sites (`tests/store/test_upsert.py`, `tests/store/test_curate.py`, patched calls in `tests/e2e/test_sync.py`) also use homogeneous batches.
  - No existing test exercises a mixed-`detail_id` batch for `upsert_position_rows`.
- Resolution carried into next step:
  - Keep this step investigation-only and proceed to Step 2 for explicit helper-level contract enforcement plus regression coverage.

### 1.x Validate Step 1
- `pytest tests/store/test_upsert.py -k position_rows -v`
- `ruff check src/`

## Step 2 — Enforce homogeneous `detail_id` contract and add regression tests
### 2.0 Pre-check findings and mitigations
- Findings in scope: `Medium-01`.
- Risks:
  - Overly broad checks may alter current idempotent replace semantics.
  - Missing regression tests may leave mixed-batch paths unprotected.
- Mitigations:
  - Enforce only the minimum contract needed: all rows in one call must share the same `detail_id`.
  - Preserve existing delete-then-insert behavior for valid homogeneous inputs.
  - Add explicit tests for mixed-`detail_id` and contract-failure behavior.

### 2.1 Add explicit batch-contract validation to `upsert_position_rows`
- Target files to edit/create:
  - `src/infn_jobs/store/upsert.py`
- Expected behavior change:
  - `upsert_position_rows` rejects heterogeneous `detail_id` batches instead of partially applying delete/insert operations.
  - Existing behavior for empty and homogeneous batches remains unchanged.
- Tests to add/update:
  - `tests/store/test_upsert.py`:
    - add a regression test for mixed `detail_id` rows in one batch,
    - assert no partial mutation occurs when contract validation fails.
- Focused verification commands:
  - `pytest tests/store/test_upsert.py -v`
  - `ruff check src/`

### 2.2 Confirm pipeline contract compatibility
- Target files to edit/create:
  - `src/infn_jobs/pipeline/sync.py` (read-only unless incompatibility discovered)
  - `tests/e2e/test_sync.py` (read-only unless incompatibility discovered)
- Expected behavior change:
  - No pipeline behavior change; current row-building flow remains compatible with stricter helper contract.
- Tests to add/update:
  - Update/add tests only if compatibility gap is discovered.
- Focused verification commands:
  - `pytest tests/e2e/test_sync.py -k position_row -v`
  - `ruff check src/`

### 2.x Validate Step 2
- `pytest tests/store/test_upsert.py tests/e2e/test_sync.py -v`
- `ruff check src/`

## Step 3 — Verification closure and contract documentation sync
### 3.0 Pre-check findings and mitigations
- Findings in scope: `Medium-01`.
- Risks:
  - Contract change lands without synchronized documentation of store-layer expectations.
  - API index regeneration may be skipped if signatures/docstrings change.
- Mitigations:
  - Add a concise contract note in architecture/conventions docs only if behavior wording changed.
  - Regenerate `docs/info_functions.md` only if public function/class signatures changed.

### 3.1 Update docs for contract-level behavior change (if required)
- Target files to edit/create:
  - `docs/plan_implementation.md` (store layer contract note, if behavior wording needs alignment)
  - `CLAUDE.md` (Key Conventions note, if shared convention changed)
  - `docs/plan_desiderata.md` (only if external behavior requirements changed; otherwise no edit)
- Expected behavior change:
  - No runtime behavior change; documentation consistency only.
- Tests to add/update:
  - None.
- Focused verification commands:
  - `rg -n "upsert_position_rows|detail_id|idempotent|store/spec" CLAUDE.md docs/plan_implementation.md docs/plan_desiderata.md`

### 3.2 Regenerate function index if API surface changed
- Target files to edit/create:
  - `docs/info_functions.md` (generated only if needed)
- Expected behavior change:
  - No runtime behavior change.
- Tests to add/update:
  - None.
- Focused verification commands:
  - `python3 scripts/gen_info_functions.py`
  - `rg -n "upsert_position_rows" docs/info_functions.md`

### 3.x Validate Step 3
- `pytest tests/ -v`
- `ruff check src/`

## Deliverables Checklist (By Finding/Requirement ID)
- `Medium-01` heterogeneous `detail_id` batch contract gap in `upsert_position_rows`: fixed via Steps 1-2; verification and doc sync in Step 3.

## Final Verification
- `pytest tests/ -v`
- `ruff check src/`
