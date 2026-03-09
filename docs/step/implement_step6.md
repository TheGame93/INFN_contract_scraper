# Step 6 — Store Layer

> **Location:** `docs/step/implement_step6.md`
> **Prerequisites:** Step 1 complete, Step 2 complete
> **Produces:**
> - `src/infn_jobs/store/schema.py`
> - `src/infn_jobs/store/upsert.py`
> - `src/infn_jobs/store/export/curate.py`
> - `src/infn_jobs/store/export/csv_writer.py`
> - `tests/conftest.py` (edited — adds `tmp_db` fixture)
> - `tests/store/test_schema.py`
> - `tests/store/test_upsert.py`
> - `tests/store/test_curate.py`
> - `tests/store/test_export.py`

Note: `tests/store/test_export.py` is not listed in `plan_implementation.md`'s test file tree
(which is approximate at ~20 files). It is added here to satisfy the policy's testing
requirement for substep 6.7 (`export_all`). The plan's `test_curate.py` covers curated-filter
behaviour; CSV export correctness is covered in `test_export.py`.

---

## 6.1 DB schema

### 6.1.1 Create `src/infn_jobs/store/schema.py`
- **File:** `src/infn_jobs/store/schema.py`
- **Action:** Create
- **Write:**
  ```python
  def init_db(conn: sqlite3.Connection) -> None:
      """Create 3 tables and 1 view with IF NOT EXISTS. Idempotent."""
  ```
- **Test:** `pytest tests/store/test_schema.py -v` (test written in sub-substep 6.2.2)
- **Notes:**
  - Create 3 tables: `calls_raw`, `position_rows`, `calls_curated`. Create 1 view: `position_rows_curated`. Use `CREATE TABLE IF NOT EXISTS` and `CREATE VIEW IF NOT EXISTS` — safe to call `init_db` twice.
  - `calls_curated` shares the identical schema with `calls_raw` (no extra columns). It is populated by `rebuild_curated()` in Step 6.6.
  - `position_rows_curated` is a **VIEW**, not a table. Per `plan_implementation.md`: it is a denormalized analytical view joining `position_rows` with `calls_curated`. The full SQL is:
    ```sql
    CREATE VIEW IF NOT EXISTS position_rows_curated AS
    SELECT
      -- linkage / status
      pr.detail_id,
      pr.position_row_index,
      c.source_tipo,
      c.listing_status,
      -- call metadata (from HTML)
      c.numero,
      c.anno,
      c.numero_posti_html,
      c.data_bando,
      c.data_scadenza,
      c.first_seen_at,
      c.last_synced_at,
      c.pdf_fetch_status,
      -- source refs
      c.detail_url,
      c.pdf_url,
      c.pdf_cache_path,
      -- derived call title
      COALESCE(c.pdf_call_title, c.titolo) AS call_title,
      -- analytics fields (from PDF)
      pr.text_quality,
      pr.contract_type,
      pr.contract_type_raw,
      pr.contract_subtype,
      pr.contract_subtype_raw,
      pr.duration_months,
      pr.duration_raw,
      pr.section_structure_department,
      pr.institute_cost_total_eur,
      pr.institute_cost_yearly_eur,
      pr.gross_income_total_eur,
      pr.gross_income_yearly_eur,
      pr.net_income_total_eur,
      pr.net_income_yearly_eur,
      pr.net_income_monthly_eur,
      -- evidence
      pr.contract_type_evidence,
      pr.contract_subtype_evidence,
      pr.duration_evidence,
      pr.section_evidence,
      pr.institute_cost_evidence,
      pr.gross_income_evidence,
      pr.net_income_evidence,
      -- quality
      pr.parse_confidence
    FROM position_rows pr
    JOIN calls_curated c ON pr.detail_id = c.detail_id;
    ```
  - `position_rows` must declare `PRIMARY KEY (detail_id, position_row_index)` and `FOREIGN KEY (detail_id) REFERENCES calls_raw(detail_id)`.
  - `calls_raw.detail_id TEXT PRIMARY KEY`. `calls_raw.numero_posti_html INTEGER`. All other `calls_raw` columns are `TEXT`.
  - `position_rows` columns include `contract_type_raw TEXT` (the original contract-type text from the PDF body, before normalization). This is distinct from `contract_type` (the canonical form). Both are `TEXT`.
  - `position_rows`: `duration_months INTEGER`; `position_row_index INTEGER`; all 7 EUR fields are `REAL`; remaining are `TEXT`. Refer to the full schema in `plan_implementation.md`.
  - **FK enforcement note:** SQLite does NOT enforce foreign keys by default (`PRAGMA foreign_keys` is OFF). The FK declarations are schema-as-documentation — they communicate the intended relationships but are not enforced at runtime. The ordering in `rebuild_curated()` is maintained for correctness if FK enforcement is later enabled. Do NOT add `PRAGMA foreign_keys = ON` — it is intentionally unenforced for simplicity.
  - Do not import from other `infn_jobs` modules — only stdlib `sqlite3`.
  - No explicit `conn.commit()` here — schema DDL is auto-committed by SQLite on each statement.

[x] done

**Substep 6.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 6.2 Schema tests

### 6.2.1 Edit `tests/conftest.py` to add `tmp_db` fixture
- **File:** `tests/conftest.py`
- **Action:** Edit
- **Write:**
  ```python
  @pytest.fixture
  def tmp_db(tmp_path: Path) -> sqlite3.Connection:
      """Yield an in-memory (or tmp-file) SQLite connection with all tables created."""
  ```
- **Test:** (no isolated test — fixture is exercised by every store test in 6.2.2, 6.5.1, 6.8.1, 6.9.1)
- **Notes:**
  - Import `sqlite3`, `pytest`, `Path` from `pathlib`, and `init_db` from `infn_jobs.store.schema`.
  - Implementation: `conn = sqlite3.connect(str(tmp_path / "test.db"))`, call `init_db(conn)`, `yield conn`, `conn.close()`.
  - Using a file-backed DB (not `:memory:`) makes it easier to inspect after a failed test.
  - This edit must be made AFTER sub-substep 6.1.1 completes, since it imports `init_db`.
  - The placeholder `conftest.py` from Step 1 contains only a comment — replace that comment with the imports and fixture definition.

[x] done

### 6.2.2 Create `tests/store/test_schema.py`
- **File:** `tests/store/test_schema.py`
- **Action:** Create
- **Write:**
  `test_init_db_creates_calls_raw_table`,
  `test_init_db_creates_position_rows_table`,
  `test_init_db_creates_calls_curated_table`,
  `test_init_db_creates_position_rows_curated_view`,
  `test_init_db_idempotent`,
  `test_calls_raw_has_expected_columns`,
  `test_position_rows_has_expected_columns`,
  `test_position_rows_has_contract_type_raw_column`
- **Test:** `pytest tests/store/test_schema.py -v`
- **Notes:**
  - Uses the `tmp_db` fixture from `conftest.py`.
  - Table existence check: `SELECT name FROM sqlite_master WHERE type='table' AND name=?`.
  - **View existence check:** `position_rows_curated` is a VIEW, not a table. Use `SELECT name FROM sqlite_master WHERE type='view' AND name='position_rows_curated'` to verify it.
  - Column check: `PRAGMA table_info(<table>)` returns rows with `name` field — collect all names and assert each expected column is present. For views, use `SELECT * FROM position_rows_curated LIMIT 0` and inspect `cursor.description` for column names.
  - `test_init_db_idempotent`: call `init_db(conn)` a second time on the same connection and assert no exception is raised and row count is unchanged.
  - `test_position_rows_has_contract_type_raw_column`: assert `contract_type_raw` is present in the `position_rows` column list (via `PRAGMA table_info(position_rows)`).
  - Do not test `calls_curated` column set separately if schema is identical to `calls_raw` — one parametrize over the 3 tables suffices for existence checks.

[x] done

**Substep 6.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/store/test_schema.py -v` passes with no failures.

---

## 6.3 `upsert_call()`

### 6.3.1 Create `src/infn_jobs/store/upsert.py`
- **File:** `src/infn_jobs/store/upsert.py`
- **Action:** Create
- **Write:**
  ```python
  def upsert_call(conn: sqlite3.Connection, call: CallRaw) -> None:
      """Upsert a CallRaw into calls_raw. Preserves first_seen_at on update."""
  ```
- **Test:** `pytest tests/store/test_upsert.py::test_upsert_call_inserts_row tests/store/test_upsert.py::test_upsert_call_first_seen_at_preserved_on_update -v` (test written in sub-substep 6.5.1)
- **Notes:**
  - Use `INSERT INTO calls_raw (...) VALUES (...) ON CONFLICT(detail_id) DO UPDATE SET ...` (SQLite ≥3.24 `UPSERT` syntax).
  - On conflict: update all fields **except** `first_seen_at` — preserve the stored value. Do NOT use `excluded.first_seen_at` in the UPDATE clause; use `calls_raw.first_seen_at` (the existing column value).
  - `first_seen_at`: on initial insert, caller must set it to `datetime.utcnow().isoformat()`. If `call.first_seen_at` is `None`, generate it inside `upsert_call` using `datetime.utcnow().isoformat()`.
  - `last_synced_at`: always set to `datetime.utcnow().isoformat()` at call time (regardless of what `call.last_synced_at` contains).
  - Call `conn.commit()` after the execute. Per CLAUDE.md: "Each upsert commits immediately."
  - Import `CallRaw` from `infn_jobs.domain.call`; import `sqlite3`, `datetime` from stdlib only.

[x] done

**Substep 6.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 6.4 `upsert_position_rows()`

### 6.4.1 Edit `src/infn_jobs/store/upsert.py` to add `upsert_position_rows()`
- **File:** `src/infn_jobs/store/upsert.py`
- **Action:** Edit
- **Write:**
  ```python
  def upsert_position_rows(conn: sqlite3.Connection, rows: list[PositionRow]) -> None:
      """Replace all position_rows for rows[0].detail_id. Deletes existing rows first."""
  ```
- **Test:** `pytest tests/store/test_upsert.py::test_upsert_position_rows_replaces_existing_rows tests/store/test_upsert.py::test_upsert_position_rows_empty_list_is_noop -v` (test written in sub-substep 6.5.1)
- **Notes:**
  - If `rows` is empty, do nothing and return (no detail_id to clear).
  - Strategy: `DELETE FROM position_rows WHERE detail_id = ?` (using `rows[0].detail_id`), then `INSERT` each row. This is a full replacement, not per-row upsert.
  - `position_row_index` is already set on each `PositionRow` by `build_rows()` — do not re-assign here.
  - Call `conn.commit()` once after all deletes and inserts (atomic replacement for one call's rows). Per CLAUDE.md: "Each upsert commits immediately" — treat the full replacement for one `detail_id` as one commit unit.
  - Import `PositionRow` from `infn_jobs.domain.position`.

[x] done

**Substep 6.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 6.5 Upsert tests

### 6.5.1 Create `tests/store/test_upsert.py`
- **File:** `tests/store/test_upsert.py`
- **Action:** Create
- **Write:**
  `test_upsert_call_inserts_row`,
  `test_upsert_call_deduplicates_on_detail_id`,
  `test_upsert_call_first_seen_at_preserved_on_update`,
  `test_upsert_call_last_synced_at_updated`,
  `test_upsert_position_rows_inserts_rows`,
  `test_upsert_position_rows_replaces_existing_rows`,
  `test_upsert_position_rows_empty_list_is_noop`
- **Test:** `pytest tests/store/test_upsert.py -v`
- **Notes:**
  - Uses the `tmp_db` fixture.
  - `test_upsert_call_inserts_row`: create `CallRaw(detail_id="1")`, call `upsert_call`, query `calls_raw` — assert 1 row with `detail_id="1"`.
  - `test_upsert_call_deduplicates_on_detail_id`: call `upsert_call` twice with same `detail_id` — assert still 1 row in `calls_raw`.
  - `test_upsert_call_first_seen_at_preserved_on_update`: insert once, record `first_seen_at`; insert again with different `titolo`; assert `first_seen_at` is unchanged and `titolo` is updated.
  - `test_upsert_call_last_synced_at_updated`: insert twice with a small `time.sleep(0.01)` between; assert `last_synced_at` on the second insert is >= the first.
  - `test_upsert_position_rows_inserts_rows`: insert a `CallRaw`, then 2 `PositionRow` objects — assert 2 rows in `position_rows` with correct `position_row_index` values (0 and 1).
  - `test_upsert_position_rows_replaces_existing_rows`: insert 2 rows, then call `upsert_position_rows` again with 3 rows — assert exactly 3 rows remain (old rows deleted, new inserted).
  - `test_upsert_position_rows_empty_list_is_noop`: call `upsert_position_rows(conn, [])` — assert no exception and `position_rows` is unchanged.

[x] done

**Substep 6.5 done when:** all sub-substeps above are `[x]` and
`pytest tests/store/test_upsert.py -v` passes with no failures.

---

## 6.6 Curated filter SQL

### 6.6.1 Create `src/infn_jobs/store/export/curate.py`
- **File:** `src/infn_jobs/store/export/curate.py`
- **Action:** Create
- **Write:**
  ```python
  def rebuild_curated(conn: sqlite3.Connection) -> None:
      """Rebuild calls_curated from the employment-like filter. position_rows_curated is a VIEW and updates automatically."""
  ```
- **Test:** `pytest tests/store/test_curate.py -v` (test written in sub-substep 6.9.1)
- **Notes:**
  - Per plan_desiderata: "Keep calls/rows matching: borsa di studio, incarico di ricerca, incarico post-doc/postdoc, contratto di ricerca, assegno di ricerca. Exclude prize-only/non-employment notices."
  - Employment-like `source_tipo` values: `'Borsa'`, `'Incarico di ricerca'`, `'Incarico Post-Doc'`, `'Contratto di ricerca'`, `'Assegno di ricerca'`. These match `TIPOS` from config.
  - Algorithm:
    1. `DELETE FROM calls_curated` — clear existing.
    2. `INSERT INTO calls_curated SELECT * FROM calls_raw WHERE source_tipo IN (...)`.
    3. `conn.commit()`.
  - `position_rows_curated` is a VIEW (defined in `init_db`), not a table. It joins `position_rows` with `calls_curated` automatically. When `calls_curated` is rebuilt, the VIEW reflects the new data without any explicit INSERT or DELETE. Do NOT attempt to INSERT into or DELETE from `position_rows_curated`.
  - This function is idempotent — calling it twice produces the same result.
  - **Future-proofing note:** In v1, the scraper only fetches the 5 employment-like tipos listed above. This means `calls_curated` will be identical to `calls_raw` in practice — the filter is not currently selective. The curated layer is retained as infrastructure for v2, which may add new source types (e.g., prizes, awards) that the filter would then exclude. Add a comment in the source file explaining this.
  - Do not import from other `infn_jobs` modules — only `sqlite3`.

[x] done

**Substep 6.6 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 6.7 CSV writer

### 6.7.1 Create `src/infn_jobs/store/export/csv_writer.py`
- **File:** `src/infn_jobs/store/export/csv_writer.py`
- **Action:** Create
- **Write:**
  ```python
  def export_all(conn: sqlite3.Connection, export_dir: Path) -> None:
      """Write 4 CSV files to export_dir from all 4 DB tables."""
  ```
- **Test:** `pytest tests/store/test_export.py -v` (test written in sub-substep 6.8.1)
- **Notes:**
  - Writes 4 files:
    - `export_dir / "calls_raw.csv"`
    - `export_dir / "calls_curated.csv"`
    - `export_dir / "position_rows_raw.csv"`
    - `export_dir / "position_rows_curated.csv"`
  - For `calls_raw` and `calls_curated` CSVs: use `SELECT *, COALESCE(pdf_call_title, titolo) AS call_title FROM <table>` — the `call_title` derived column appears in the CSV but is NOT stored in the DB. Per plan_implementation.md: "The `call_title` column in CSV exports is a derived field: `COALESCE(pdf_call_title, titolo)`. It is not stored as a separate DB column."
  - For `position_rows_*` CSVs: `SELECT * FROM <table>` — all columns including `detail_id` and `position_row_index` on every row.
  - Use Python's `csv.writer` with `newline=""` and UTF-8 encoding. Write column headers from `cursor.description`.
  - Create `export_dir` if it does not exist: `export_dir.mkdir(parents=True, exist_ok=True)`.
  - Log at INFO: `"Exported {n} rows to {filename}"` for each CSV.
  - Do not import from other `infn_jobs` modules except `pathlib.Path` — only stdlib.

[x] done

**Substep 6.7 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 6.8 Export tests

### 6.8.1 Create `tests/store/test_export.py`
- **File:** `tests/store/test_export.py`
- **Action:** Create
- **Write:**
  `test_export_all_creates_four_csv_files`,
  `test_export_calls_raw_csv_nonempty`,
  `test_export_calls_raw_csv_has_call_title_column`,
  `test_export_calls_raw_csv_columns_complete`,
  `test_export_position_rows_csv_has_detail_id_and_index`
- **Test:** `pytest tests/store/test_export.py -v`
- **Notes:**
  - Uses the `tmp_db` fixture plus `tmp_path` for the export directory.
  - Before calling `export_all`, insert at least one `CallRaw` (with `upsert_call`) and call `rebuild_curated` so all 4 tables have data.
  - `test_export_all_creates_four_csv_files`: after `export_all(conn, tmp_path)`, assert all 4 expected filenames exist under `tmp_path`.
  - `test_export_calls_raw_csv_nonempty`: open `calls_raw.csv`, assert it has at least 2 lines (header + 1 data row).
  - `test_export_calls_raw_csv_has_call_title_column`: read the header row of `calls_raw.csv`, assert `"call_title"` is present.
  - `test_export_calls_raw_csv_columns_complete`: assert `"detail_id"`, `"source_tipo"`, `"pdf_fetch_status"` are all in the header row.
  - `test_export_position_rows_csv_has_detail_id_and_index`: read `position_rows_raw.csv` header, assert both `"detail_id"` and `"position_row_index"` are present.

[x] done

**Substep 6.8 done when:** all sub-substeps above are `[x]` and
`pytest tests/store/test_export.py -v` passes with no failures.

---

## 6.9 Curated filter tests

### 6.9.1 Create `tests/store/test_curate.py`
- **File:** `tests/store/test_curate.py`
- **Action:** Create
- **Write:**
  `test_rebuild_curated_keeps_employment_calls`,
  `test_rebuild_curated_excludes_unknown_source_tipo`,
  `test_rebuild_curated_populates_calls_curated`,
  `test_rebuild_curated_view_reflects_curated_calls`,
  `test_rebuild_curated_idempotent`
- **Test:** `pytest tests/store/test_curate.py -v`
- **Notes:**
  - Uses the `tmp_db` fixture.
  - Setup: insert 2 `CallRaw` objects — one with `source_tipo="Borsa"` (employment-like) and one with `source_tipo="Premio"` (unknown/non-employment). For the `Borsa` call, also insert 2 `PositionRow` objects via `upsert_position_rows`.
  - `test_rebuild_curated_keeps_employment_calls`: after `rebuild_curated`, assert `calls_curated` contains the `"Borsa"` call (detail_id matches).
  - `test_rebuild_curated_excludes_unknown_source_tipo`: assert the `"Premio"` call is NOT in `calls_curated`.
  - `test_rebuild_curated_populates_calls_curated`: assert `SELECT COUNT(*) FROM calls_curated` == 1.
  - `test_rebuild_curated_view_reflects_curated_calls`: assert `SELECT COUNT(*) FROM position_rows_curated` == 2 (the 2 position_rows from the employment call). This tests the VIEW — `position_rows_curated` is not populated by `rebuild_curated()` but automatically reflects the join between `position_rows` and `calls_curated`.
  - `test_rebuild_curated_idempotent`: call `rebuild_curated` twice — assert row counts are the same after both calls (no duplication).

[x] done

**Substep 6.9 done when:** all sub-substeps above are `[x]` and
`pytest tests/store/test_curate.py -v` passes with no failures.

---

## Verification

```bash
pytest tests/store/ -v
ruff check src/infn_jobs/store/
```

Expected: all store layer tests green, ruff exits 0.

Manual checks:
- `python3 -c "from infn_jobs.store.schema import init_db; from infn_jobs.store.upsert import upsert_call, upsert_position_rows; from infn_jobs.store.export.curate import rebuild_curated; from infn_jobs.store.export.csv_writer import export_all; print('store OK')"` prints `store OK`.
- Create a temporary DB: `python3 -c "import sqlite3; from infn_jobs.store.schema import init_db; conn = sqlite3.connect(':memory:'); init_db(conn); print('tables:', [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]); print('views:', [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='view'\").fetchall()])"` — prints 3 table names (`calls_raw`, `position_rows`, `calls_curated`) and 1 view name (`position_rows_curated`).
