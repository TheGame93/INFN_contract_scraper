# Step 9 — End-to-End Verification

> **Location:** `docs/step/implement_step9.md`
> **Prerequisites:** Steps 1–8 complete
> **Produces:**
> - `tests/e2e/test_sync.py`

Note: `docs/info_functions.md` is generated (not hand-edited) — substep 9.3.2 runs the script
and commits the output. It is not listed in Produces because it is a generated artifact, not a
source file.

---

## 9.1 Write `tests/e2e/test_sync.py`

### 9.1.1 Create `tests/e2e/test_sync.py`
- **File:** `tests/e2e/test_sync.py`
- **Action:** Create
- **Write:**
  `test_sync_runs_without_error`,
  `test_sync_db_has_calls_across_tipos`,
  `test_sync_is_idempotent`,
  `test_first_seen_at_immutable`,
  `test_last_synced_at_updated`,
  `test_export_csv_creates_four_files`,
  `test_position_row_count_exceeds_call_count`,
  `test_no_text_produces_zero_position_rows`,
  `test_ocr_degraded_produces_low_confidence_rows`
- **Test:** `pytest tests/e2e/test_sync.py -v`
- **Notes:**
  - **Test strategy:** patch the network and subprocess layers so the test is deterministic and fast.
    The real store (schema, upsert), pipeline (`run_sync`, `build_rows`), and export layers run
    without mocking — only the I/O boundaries are stubbed. This validates the wiring and data-flow
    contracts that unit tests cannot cover.
  - **Imports needed in the test file:**
    - stdlib: `import sqlite3`, `import time`, `from pathlib import Path`, `from unittest.mock import patch, MagicMock`
    - pytest: `import pytest`
    - project: `from infn_jobs.store.schema import init_db`, `from infn_jobs.pipeline.sync import run_sync`, `from infn_jobs.pipeline.export import run_export`, `from infn_jobs.domain.call import CallRaw`, `from infn_jobs.domain.enums import TextQuality`
  - **Fixture setup (shared via module-level helper or `@pytest.fixture`):**
    - Load the text content of `tests/fixtures/pdf_text/multi_same_type.txt` into a variable
      `MULTI_TEXT: str`. This fixture must exist (created in Step 5.8).
    - Define `make_calls() -> list[CallRaw]` — returns one `CallRaw` per TIPO:
      - For `source_tipo = "Borsa"`: `CallRaw(detail_id="e2e-borsa-1", source_tipo="Borsa", listing_status="active", pdf_url="https://jobs.dsi.infn.it/bando.pdf", anno="2022")`
      - For `source_tipo = "Assegno di ricerca"`: `CallRaw(detail_id="e2e-assegno-1", source_tipo="Assegno di ricerca", listing_status="active", pdf_url=None, anno="2005")`
      - For the remaining 3 tipos: simple `CallRaw(detail_id=f"e2e-{i}", source_tipo=tipo, listing_status="expired", pdf_url="https://jobs.dsi.infn.it/bando2.pdf", anno="2015")`
      — total of 5 `CallRaw` objects (one per tipo).
    - `make_calls()` is called inside the mock's `side_effect` so the same objects are returned
      on every `fetch_all_calls` call: `mock_fac.side_effect = lambda session, tipo: [c for c in make_calls() if c.source_tipo == tipo]`.
  - **Patch targets** (must match the names as imported in `infn_jobs/pipeline/sync.py`):
    - `"infn_jobs.pipeline.sync.fetch_all_calls"` — return the appropriate `CallRaw` for the tipo.
    - `"infn_jobs.pipeline.sync.download"` — return a `Path` object (e.g., `tmp_path / "mock.pdf"`) for calls with a `pdf_url`; use `side_effect` to return `None` when `call.pdf_url` would have been `None` (but since the skip branch checks `call.pdf_url is None` before calling `download`, this mock is only invoked for calls with a URL — return a valid path unconditionally).
    - `"infn_jobs.pipeline.sync.extract_text"` — return `(MULTI_TEXT, TextQuality.DIGITAL)` (import `TextQuality` from `infn_jobs.domain.enums`). The pipeline converts the enum to string via `.value` before passing to `build_rows`.
    - The mocked `download` path does not need to be a real PDF file — `extract_text` is also mocked, so the path is never opened.
  - **`test_sync_runs_without_error`:**
    - Apply patches; call `run_sync(conn, dry_run=False, force_refetch=False)`.
    - Assert no exception is raised.
    - `conn = sqlite3.connect(str(tmp_path / "test.db"))` + `init_db(conn)` — use `tmp_path` from pytest.
  - **`test_sync_db_has_calls_across_tipos`:**
    - After `run_sync`, query `SELECT COUNT(*) FROM calls_raw` — assert count == 5 (one per tipo).
    - Query `SELECT DISTINCT source_tipo FROM calls_raw` — assert all 5 TIPOS are present.
  - **`test_sync_is_idempotent`:**
    - Run `run_sync` twice on the same `conn`.
    - After first run: record `first_count_calls = SELECT COUNT(*) FROM calls_raw` and `first_count_rows = SELECT COUNT(*) FROM position_rows`.
    - After second run: assert `SELECT COUNT(*) FROM calls_raw == first_count_calls` and `SELECT COUNT(*) FROM position_rows == first_count_rows`.
  - **`test_first_seen_at_immutable`:**
    - Run `run_sync` once; query and store `first_seen_at` for `detail_id="e2e-borsa-1"`.
    - Sleep `time.sleep(0.05)` to advance wall time.
    - Run `run_sync` again; re-query `first_seen_at` for the same `detail_id`.
    - Assert the two values are equal (string comparison — both are ISO-format datetimes).
  - **`test_last_synced_at_updated`:**
    - Run `run_sync` once; record `last1 = SELECT last_synced_at FROM calls_raw WHERE detail_id="e2e-borsa-1"`.
    - Sleep `time.sleep(0.05)`.
    - Run `run_sync` again; record `last2`.
    - Assert `last2 >= last1` (string comparison is valid for ISO-format UTC datetimes).
  - **`test_export_csv_creates_four_files`:**
    - Run `run_sync`; then run `run_export(conn, export_dir)` where `export_dir = tmp_path / "exports"`.
    - Assert all 4 files exist: `calls_raw.csv`, `calls_curated.csv`, `position_rows_raw.csv`, `position_rows_curated.csv`.
    - Assert each file has at least 2 lines (header + at least 1 data row).
    - Note: `run_export` calls `rebuild_curated` internally, so no separate call is needed. `position_rows_curated` is a VIEW and reflects the join automatically.
  - **`test_position_row_count_exceeds_call_count`:**
    - After `run_sync`, query `SELECT COUNT(*) FROM calls_raw AS nc` and `SELECT COUNT(*) FROM position_rows AS nr`.
    - Assert `nr > nc`. This holds because the mocked `extract_text` returns `MULTI_TEXT` (which `segment()` splits into >1 segment → >1 `PositionRow` per PDF call). At least the 4 calls with `pdf_url` set produce multiple rows.
    - This test validates the one-to-many pipeline end-to-end: `calls_raw` → `position_rows` via `build_rows`.
  - **`test_no_text_produces_zero_position_rows`:**
    - Use a separate `conn` and `tmp_path`. Patch `extract_text` to return `("", TextQuality.NO_TEXT)` instead of `(MULTI_TEXT, TextQuality.DIGITAL)`.
    - Patch `fetch_all_calls` to return a single `CallRaw` with `pdf_url` set.
    - Run `run_sync(conn)`.
    - Assert `SELECT COUNT(*) FROM position_rows` == 0 (per CLAUDE.md: `no_text` → 0 position_rows).
    - Assert `SELECT pdf_fetch_status FROM calls_raw WHERE detail_id=...` == `"ok"` (download and mutool both succeeded; the PDF simply has no text).
  - **`test_ocr_degraded_produces_low_confidence_rows`:**
    - Use a separate `conn` and `tmp_path`. Patch `extract_text` to return `("<garbled OCR text with some structure>", TextQuality.OCR_DEGRADED)`. Use a minimal text string that `segment()` can split into at least 1 segment.
    - Patch `fetch_all_calls` to return a single `CallRaw` with `pdf_url` set.
    - Run `run_sync(conn)`.
    - Assert `SELECT COUNT(*) FROM position_rows` >= 1 (extraction is attempted for `ocr_degraded`).
    - Assert all rows have `parse_confidence = "low"` and `text_quality = "ocr_degraded"`.
  - **Parametrize note:** do not parametrize tests that share state (DB connection). Run each test with an independent `tmp_path` to avoid inter-test interference.
  - **`tests/e2e/` directory** was created in Step 1 (`.gitkeep`). Remove the `.gitkeep` file when this test file is created, or simply create the test file and let git track it instead of the placeholder.

[x] done

**Substep 9.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/e2e/ -v` passes with no failures.

---

## 9.2 Run full verification checklist

### 9.2.1 Run the full verification checklist from `docs/plan_implementation.md`
- **File:** (no source file — verification against the live system)
- **Action:** (verification)
- **Write:** (no code — run each checklist item below and confirm expected output)
- **Test:** (manual verification — execute all 9 items from `plan_implementation.md § Verification Checklist`:
  1. `python3 -m infn_jobs sync` completes without error; `data/infn_jobs.db` exists; `SELECT COUNT(*), source_tipo FROM calls_raw GROUP BY source_tipo` returns rows for all 5 source types.
  2. Run `python3 -m infn_jobs sync` a second time; `SELECT COUNT(*) FROM calls_raw` and `SELECT COUNT(*) FROM position_rows` are identical to the first run.
  3. `SELECT detail_id, first_seen_at, last_synced_at FROM calls_raw LIMIT 5` — confirm `first_seen_at` values match the first run and `last_synced_at` values are more recent.
  4. `SELECT COUNT(*) FROM calls_raw WHERE pdf_fetch_status = "skipped"` returns > 0 (old records without PDF links exist).
  5. `SELECT DISTINCT text_quality FROM position_rows` — confirm at least `"digital"` is present; `SELECT detail_id FROM position_rows WHERE text_quality = "ocr_degraded" AND parse_confidence != "low"` returns 0 rows (degraded quality → low confidence). Note: `no_text` PDFs produce 0 `position_rows` (no rows to check), so `text_quality = "no_text"` should NOT appear in `position_rows`.
  6. `python3 -m infn_jobs export-csv` completes; `ls data/exports/` shows all 4 CSV files with non-zero size.
  7. Open `data/exports/position_rows_curated.csv` — confirm every data row has non-empty `detail_id` and `position_row_index` columns.
  8. `SELECT detail_id, COUNT(*) AS n FROM position_rows GROUP BY detail_id HAVING n > 1 LIMIT 3` returns at least 1 row (multi-entry PDF exists in dataset).
  9. `pytest tests/ -v` — zero failures.)
- **Notes:**
  - Items 1–8 require a live `data/infn_jobs.db` populated by at least one full `sync` run against `jobs.dsi.infn.it`. The DB is not committed to the repository — run this verification on the development machine.
  - SQLite queries can be run via `python3 -c "import sqlite3; conn = sqlite3.connect('data/infn_jobs.db'); print(conn.execute('...').fetchall())"` or via any SQLite browser.
  - If any checklist item fails, diagnose the root cause before marking this substep `[x]`. Document any new failure pattern in `docs/known_edge_cases.md`.
  - Item 9 (`pytest tests/ -v`) must pass with the real DB absent — the unit tests use tmp databases and fixture files, so they must not depend on `data/infn_jobs.db`.

[x] done

**Substep 9.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 9.3 Generate `docs/info_functions.md`

Note: `scripts/gen_info_functions.py` already exists (written before implementation began).
This substep runs it after all source files are in place and verifies the output is complete.

### 9.3.1 Run `gen_info_functions.py` and verify output
- **File:** `docs/info_functions.md`
- **Action:** (generated — no manual edit)
- **Write:** (run the script; output is auto-generated)
- **Test:** (manual verification —
  1. `python3 scripts/gen_info_functions.py` exits 0.
  2. Open `docs/info_functions.md` — confirm entries exist for every public function listed below (spot-check at least 5):
     `init_data_dirs`, `build_parser`, `run`, `fetch_all_calls`, `parse_rows`, `parse_detail`,
     `build_urls`, `get_session`, `download`, `extract_text`, `segment`, `build_rows`,
     `normalize_eur`, `parse_date`, `normalize_subtype`, `init_db`, `upsert_call`,
     `upsert_position_rows`, `rebuild_curated`, `export_all`, `run_export`, `score_confidence`.
  3. Confirm entries are sorted by file path.
  4. Confirm no entry has `"(no docstring)"` — if any appear, add the missing docstring to the source file and re-run the script.)
- **Notes:**
  - If any function shows `"(no docstring)"`, that is a docstring violation — fix the source first, then re-run. Per CLAUDE.md: "Every public function, method, and class must have a one-line docstring."
  - Commit both `scripts/gen_info_functions.py` and the generated `docs/info_functions.md` together.
  - Re-run the script whenever functions are added, renamed, or removed. Add `python3 scripts/gen_info_functions.py` as a reminder in the commit checklist (or as a pre-commit hook if desired).

[x] done

**Substep 9.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 9.4 Mark all steps `[x]`

### 9.4.1 Mark all steps and substeps `[x]` in `docs/step/planning_step.md`
- **File:** `docs/step/planning_step.md`
- **Action:** Edit
- **Write:** (no code — update status markers)
- **Test:** (manual verification — open `docs/step/planning_step.md` and confirm every `[ ]` and `[~]` marker under the Step Index is now `[x]`; confirm the Completion Summary table shows `[x]` for all 9 steps; update `## Currently Active` to "All steps complete")
- **Notes:**
  - Per policy_step.md: mark `[x]` only after the verification command passes for each item. Do not pre-mark.
  - Also mark all sub-substeps `[x]` in their respective `implement_stepN.md` files as each is completed during implementation. Substep 9.4 marks the final tracker update in `planning_step.md` — the implement files are updated incrementally throughout the project.
  - The Completion Summary table in `planning_step.md` should go from all `[ ]` to all `[x]` as the final act of this step.
  - Update `## Currently Active` section to: `> **All steps complete.** No active sub-substep.`

[x] done

**Substep 9.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## Verification

```bash
pytest tests/ -v
ruff check src/
```

Expected: all tests (unit + e2e) green, ruff exits 0.

Manual checks (require a live `data/infn_jobs.db` from a completed `sync` run):
- `python3 -m infn_jobs sync` exits 0; second run exits 0; `SELECT COUNT(*) FROM calls_raw` is identical before and after the second run.
- `python3 -m infn_jobs export-csv` exits 0; `data/exports/` contains 4 non-empty CSV files.
- `SELECT COUNT(*) FROM calls_raw WHERE pdf_fetch_status = "skipped"` > 0.
- `SELECT detail_id, COUNT(*) AS n FROM position_rows GROUP BY detail_id HAVING n > 1 LIMIT 1` returns at least 1 row.
- `cat data/exports/position_rows_curated.csv | head -2` shows both `detail_id` and `position_row_index` in the header.
- `docs/info_functions.md` contains an entry for every public function in `src/infn_jobs/`.
- `docs/step/planning_step.md` Completion Summary shows `[x]` for all 9 steps.
