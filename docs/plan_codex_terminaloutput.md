# Sync Terminal Output and Runtime Observability Plan

## Inputs and truth references
- User-provided specification in this thread (terminal-noise reduction + logfile + runtime heartbeat/timing expectations).
- `CLAUDE.md`
- `docs/plan_desiderata.md`
- `docs/plan_implementation.md`
- `docs/info_functions.md`
- `docs/step/policy_step.md`
- `docs/step/planning_step.md`
- `src/infn_jobs/cli/main.py`
- `src/infn_jobs/pipeline/sync.py`
- `src/infn_jobs/config/settings.py`
- `README.md`
- `.gitignore`
- `tests/cli/test_main.py`
- `tests/e2e/test_sync.py`
- `tests/pipeline/test_sync_policy.py`
- `tests/fetch/test_orchestrator.py`

## Execution order
1. Lock runtime-output contract and risk gates first (counter semantics, terminal-vs-logfile split, interruption behavior) before editing handlers, to avoid broad logging regressions.
2. Build logging sink infrastructure (log directory/path and CLI handler wiring) next, because all downstream runtime-output behavior depends on this boundary.
3. Add sync runtime progress/timing emission with deterministic heartbeat cadence and source-mode parity, then align focused tests.
4. Synchronize docs and run full verification only after behavior and tests stabilize, minimizing doc churn and rollback risk.

## Implementation Checklist
- [x] Step 1 — Investigation gate and runtime output contract lock (`R01`, `R03`, `R04`, `R06`, `R07`, `R09`)
- [x] Step 2 — CLI/file logging split and runtime artifact directory wiring (`R01`, `R02`, `R05`, `R10`)
- [ ] Step 3 — Sync runtime heartbeat, phase timings, and final summary counters (`R03`, `R04`, `R06`, `R07`, `R08`)
- [ ] Step 4 — Regression tests and docs synchronization (`R08`, `R09`, `R10`, `R11`)

## Step 1 — Investigation gate and runtime output contract lock (`R01`, `R03`, `R04`, `R06`, `R07`, `R09`)
### 1.0 Pre-check findings and mitigations
- Finding `S1-F01`: `cli/main.py` configures root logging at INFO to terminal; all module INFO records currently flood stdout.
- Resolution `S1-F01`: define a strict output split contract in plan/tests: terminal gets runtime progress + warning/error only; detailed INFO remains in logfile.
- Finding `S1-F02`: sync phases already exist but expose only verbose INFO statements, not concise progress lines with deterministic counters/timings.
- Resolution `S1-F02`: define explicit runtime-message events and field set before handler changes.
- Finding `S1-F03`: caplog tests currently assert specific INFO messages (e.g., throttle reminder) and may break with handler/level changes.
- Resolution `S1-F03`: isolate runtime-output assertions from diagnostic INFO assertions and keep warning/error behavior unchanged.
- Finding `S1-F04`: no configured log artifact directory under `data/`; adding logs can create accidental git noise.
- Resolution `S1-F04`: add explicit log artifact ignore rule + directory skeleton policy.
- Finding `S1-F05`: per-detail INFO logs are emitted from both `pipeline.sync` and `fetch.orchestrator`; terminal filtering by level alone would hide required runtime heartbeat lines or still leak noisy INFO.
- Resolution `S1-F05`: reserve a dedicated runtime-status logging channel (distinct logger identity and/or filter key) so terminal can show only runtime lines while all generic INFO remains file-only.
- Finding `S1-F06`: lowering logger levels to quiet terminal would break INFO-based regression assertions and reduce logfile diagnostic value.
- Resolution `S1-F06`: keep logger emission levels at INFO for diagnostics, and perform suppression only at terminal-handler filter level.
- Finding `S1-F07`: `processed_contracts` is ambiguous across normal, `download_only`, `dry_run`, and interrupted runs.
- Resolution `S1-F07`: lock `processed_contracts` as the number of sync work items discovered for this run (`len(items)`), and require summary counters to distinguish outcomes (`ok`, `skipped`, `download_error`, `parse_error`, plus partial-run note for interruption paths).

### 1.1 Define deterministic runtime output contract
- Target files to edit/create:
  - `docs/plan_codex_terminaloutput.md` (this plan; contract section remains source of truth during implementation)
- Expected behavior change:
  - No runtime code change yet.
  - Lock the runtime contract:
    - heartbeat cadence: every 250 processed contracts,
    - terminal line classes: start, periodic heartbeat, phase completion timings, final summary,
    - final summary counters for outcome visibility across all source modes,
    - mandatory logfile path disclosure in terminal start line.
- Tests to add/update:
  - None (investigation-only gate).
- Focused verification commands:
  - `rg -n "Phase A:|Phase B:|Phase C:|Phase D:|Processing detail_id|Throttle reminder" src/infn_jobs/pipeline/sync.py`
  - `rg -n "logging.basicConfig|caplog.at_level\(\"INFO\", logger=\"infn_jobs.pipeline.sync\"" tests/cli/test_main.py tests/e2e/test_sync.py`

### 1.2 Confirm processed-contract semantics and early-exit coverage
- Target files to edit/create:
  - `src/infn_jobs/pipeline/sync.py` (read-only in this gate)
  - `tests/e2e/test_sync.py` (read-only in this gate)
- Expected behavior change:
  - No runtime code change yet.
  - Decide and lock counting semantics for `processed_contracts` so they are stable for:
    - full run,
    - `download_only=True` early return,
    - `dry_run=True` early return,
    - interruption path (`KeyboardInterrupt`).
  - Decision locked in this step: `processed_contracts = len(items)` where `items` is the discovered `_SyncWorkItem` list for the run; summaries must include status counters so users can distinguish parsing/persistence outcomes from total discovered workload.
- Tests to add/update:
  - None yet; this substep defines assertions required in Step 3/4.
- Focused verification commands:
  - `rg -n "download_only=True|dry_run=True|KeyboardInterrupt|run_sync\(" src/infn_jobs/pipeline/sync.py tests/e2e/test_sync.py`

### 1.3 Requirement status map from investigation gate
- Target files to edit/create:
  - `docs/plan_codex_terminaloutput.md` (status map only).
- Expected behavior change:
  - No runtime code change.
  - Requirement classification locked from current code/tests:
    - `R01`: missing (terminal still receives generic INFO spam).
    - `R02`: missing (no per-run logfile path or log artifact directory).
    - `R03`: missing (no heartbeat contract; only verbose INFO lines).
    - `R04`: partially covered (phase labels exist, phase elapsed times absent).
    - `R05`: missing (`data/logs` path/ignore policy absent).
    - `R06`: unclear/theoretical risk (counter semantics not defined).
    - `R07`: partially covered (throttle reminder exists; interruption summary semantics missing).
    - `R08`: missing (source-parity runtime output contract not defined).
    - `R09`: partially covered (log tests exist but brittle against handler refactor).
    - `R10`: missing (artifact/documentation sync not implemented for new log outputs).
    - `R11`: missing (documentation/function-index sync not yet applied to this feature).
- Tests to add/update:
  - None (investigation-only).
- Focused verification commands:
  - `rg -n "R0[1-9]|R10|R11" docs/plan_codex_terminaloutput.md`

### 1.x Validate Step 1
- `rg -n "R0[1-9]|R10|R11" docs/plan_codex_terminaloutput.md`
- `rg -n "S1-F0[1-7]" docs/plan_codex_terminaloutput.md`

## Step 2 — CLI/file logging split and runtime artifact directory wiring (`R01`, `R02`, `R05`, `R10`)
### 2.0 Pre-check findings and mitigations
- Finding `S2-F01`: replacing `basicConfig` behavior can inadvertently suppress warning/error visibility.
- Resolution `S2-F01`: keep warning/error flow on terminal via explicit stream handler thresholds/filters; verify with focused tests.
- Finding `S2-F02`: logging setup is currently centralized in `cli/main.py`; adding complex setup can bloat `run()`.
- Resolution `S2-F02`: keep orchestration in CLI layer and extract dedicated helper(s) with clear docstrings.
- Finding `S2-F03`: repeated `run()` calls in the same interpreter (unit tests) can accumulate root handlers and duplicate log emission.
- Resolution `S2-F03`: clear and close existing root handlers before attaching the new terminal/file handlers.
- Finding `S2-F04`: second-level timestamp naming can collide when multiple sync runs start within the same second.
- Resolution `S2-F04`: use higher-resolution timestamp suffix for logfile naming (microseconds) to keep per-run paths deterministic and unique.
- Finding `S2-F05`: configuring file logging before runtime directories exist risks `FileHandler` failures.
- Resolution `S2-F05`: ensure `init_data_dirs()` is executed before logging handler setup in CLI run flow.

### 2.1 Add log artifact directory + deterministic logfile naming inputs
- Target files to edit/create:
  - `src/infn_jobs/config/settings.py`
  - `.gitignore`
  - `data/logs/.gitkeep` (new)
- Expected behavior change:
  - Runtime creates/uses `data/logs/` as log artifact location.
  - Log files are treated as runtime artifacts (ignored by git).
- Tests to add/update:
  - `tests/config/test_settings.py` (add assertion for log directory initialization behavior).
- Focused verification commands:
  - `pytest tests/config/test_settings.py -v`
  - `ruff check src/infn_jobs/config/settings.py`

### 2.2 Refactor CLI logging setup into explicit terminal/file handlers
- Target files to edit/create:
  - `src/infn_jobs/cli/main.py`
  - `tests/cli/test_main.py`
- Expected behavior change:
  - Detailed INFO logs are routed to logfile handler.
  - Terminal suppresses generic INFO spam while keeping warning/error and runtime-status lines.
  - Startup still initializes logging before command dispatch; fatal-error stderr behavior remains unchanged.
- Tests to add/update:
  - Extend `tests/cli/test_main.py` to assert logging setup path and handler construction behavior instead of only `basicConfig` invocation.
- Focused verification commands:
  - `pytest tests/cli/test_main.py -v`
  - `ruff check src/infn_jobs/cli/main.py`

### 2.x Validate Step 2
- `pytest tests/config/test_settings.py tests/cli/test_main.py -v`
- `ruff check src/infn_jobs/config/settings.py src/infn_jobs/cli/main.py`

## Step 3 — Sync runtime heartbeat, phase timings, and final summary counters (`R03`, `R04`, `R06`, `R07`, `R08`)
### 3.0 Pre-check findings and mitigations
- Finding `S3-F01`: terminal progress must cover all source flows without introducing `print()` in library code.
- Resolution `S3-F01`: emit runtime status via logger records from `pipeline/sync.py` using logger-based policy only.
- Finding `S3-F02`: per-item heartbeat logic can drift between parse/materialize phases and under-report on small runs.
- Resolution `S3-F02`: centralize heartbeat counter updates and always emit deterministic final summary even when totals are below heartbeat threshold.
- Finding `S3-F03`: interruption path currently guarantees throttle reminder via `finally`; new summary lines may be skipped.
- Resolution `S3-F03`: preserve throttle reminder guarantee and add interruption-safe summary contract where feasible without swallowing interruption.

### 3.1 Introduce runtime progress events and phase timers in sync pipeline
- Target files to edit/create:
  - `src/infn_jobs/pipeline/sync.py`
- Expected behavior change:
  - Emit concise runtime status lines for:
    - sync start (including source and logfile path supplied by CLI context),
    - phase-level elapsed durations for A/B/C/D,
    - heartbeat every 250 processed contracts,
    - final summary with processed total, outcome counters, and total elapsed time.
  - Keep existing sync semantics unchanged (`source`, `dry_run`, `download_only`, idempotency behavior).
- Tests to add/update:
  - `tests/e2e/test_sync.py` (add assertions for runtime summary/heartbeat presence and early-exit consistency).
- Focused verification commands:
  - `pytest tests/e2e/test_sync.py -k "sync_logs_throttle_reminder or dry_run or download_only or source=auto" -v`
  - `ruff check src/infn_jobs/pipeline/sync.py`

### 3.2 Preserve warning/error visibility and throttle guidance in reduced-noise mode
- Target files to edit/create:
  - `src/infn_jobs/pipeline/sync.py`
  - `tests/e2e/test_sync.py`
  - `tests/pipeline/test_sync_policy.py` (if logger-level assumptions need alignment)
- Expected behavior change:
  - Warning anomalies (orphan cache, missing cache, zero-byte cache) remain visible on terminal.
  - Throttle reminder remains emitted on success and interruption.
- Tests to add/update:
  - Update any failing caplog assertions to match new runtime-output contract while preserving semantic checks.
- Focused verification commands:
  - `pytest tests/e2e/test_sync.py tests/pipeline/test_sync_policy.py -v`
  - `ruff check src/infn_jobs/pipeline/sync.py`

### 3.x Validate Step 3
- `pytest tests/e2e/test_sync.py tests/pipeline/test_sync_policy.py tests/fetch/test_orchestrator.py -v`
- `ruff check src/infn_jobs/pipeline/sync.py src/infn_jobs/cli/main.py`

## Step 4 — Regression tests and docs synchronization (`R08`, `R09`, `R10`, `R11`)
### 4.0 Pre-check findings and mitigations
- Finding `S4-F01`: user-facing docs do not describe logfile location or reduced terminal output behavior.
- Resolution `S4-F01`: update command docs and runtime artifacts section with explicit expectations.
- Finding `S4-F02`: conventions doc currently states CLI config via `basicConfig(INFO)`; this will drift after handler refactor.
- Resolution `S4-F02`: update `CLAUDE.md` logging standard to match final architecture.

### 4.1 Update docs for new runtime-observability behavior
- Target files to edit/create:
  - `README.md`
  - `CLAUDE.md`
  - `docs/plan_desiderata.md`
  - `docs/plan_implementation.md`
- Expected behavior change:
  - No runtime code change.
  - Docs explain:
    - concise terminal output policy,
    - per-run logfile location under `data/logs/`,
    - heartbeat/timing summary expectations,
    - unchanged sync source semantics.
- Tests to add/update:
  - None (doc sync only).
- Focused verification commands:
  - `rg -n "logfile|data/logs|heartbeat|runtime|terminal|warning" README.md CLAUDE.md docs/plan_desiderata.md docs/plan_implementation.md`

### 4.2 Regenerate function index and validate no CSV schema impact
- Target files to edit/create:
  - `docs/info_functions.md` (generated only if function/class surface changes)
  - `docs/info_csvfields.md` (expected no-op; verify unchanged)
- Expected behavior change:
  - No runtime behavior change.
  - Function index reflects any newly introduced helpers in CLI/pipeline.
- Tests to add/update:
  - None (consistency-only).
- Focused verification commands:
  - `python3 scripts/gen_info_functions.py`
  - `git diff -- docs/info_functions.md docs/info_csvfields.md`

### 4.x Validate Step 4
- `pytest tests/ -v`
- `ruff check src/`

## Deliverables Checklist (By Finding/Requirement ID)
- `R01` — fixed via Steps 1–2 (terminal noise suppression by splitting terminal/logfile outputs).
- `R02` — fixed via Step 2 (per-run logfile artifact path under `data/logs/` + ignore policy).
- `R03` — fixed via Step 3 (compact start + heartbeat runtime lines).
- `R04` — fixed via Step 3 (phase elapsed timings A/B/C/D + total elapsed summary).
- `R05` — fixed via Step 2 and Step 4 (runtime artifact directory wiring + repo ignore/doc sync).
- `R06` — fixed via Step 3 (stable processed-contract counter semantics across source modes and early exits).
- `R07` — fixed via Step 3 (interrupt-safe summary/throttle messaging with warning/error visibility preserved).
- `R08` — fixed via Steps 3–4 (all source modes receive same runtime contract with focused regression coverage).
- `R09` — fixed via Steps 1, 3, and 4 (test alignment for log assertions, avoiding brittle INFO-capture regressions).
- `R10` — fixed via Steps 2 and 4 (git-noise prevention and public artifact/documentation alignment).
- `R11` — fixed via Step 4 (documentation + optional function-index regeneration workflow).

## Final Verification
- `pytest tests/ -v`
- `ruff check src/`
