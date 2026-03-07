# Step 7 — Pipeline Layer

> **Location:** `docs/step/implement_step7.md`
> **Prerequisites:** Step 2 complete, Step 3 complete, Step 4 complete, Step 5 complete, Step 6 complete
> **Produces:**
> - `src/infn_jobs/pipeline/curate.py`
> - `src/infn_jobs/pipeline/sync.py`

Note: the pipeline layer has **no dedicated unit tests** — per `planning_step.md`: "covered by e2e in Step 9."
All sub-substep verification is therefore manual. The `__init__.py` for `pipeline/` was created in Step 1.

---

## 7.1 `pipeline/curate.py` — thin wrapper

### 7.1.1 Create `src/infn_jobs/pipeline/curate.py`
- **File:** `src/infn_jobs/pipeline/curate.py`
- **Action:** Create
- **Write:**
  ```python
  def rebuild_curated(conn: sqlite3.Connection) -> None:
      """Rebuild curated tables. Delegates to store.export.curate."""
  ```
- **Test:** (manual verification — `python3 -c "from infn_jobs.pipeline.curate import rebuild_curated; print('pipeline curate OK')"` prints `pipeline curate OK` with no import error)
- **Notes:**
  - This is a pure delegation wrapper. Its only logic is:
    1. Log `logger.info("Rebuilding curated tables …")`.
    2. Call `store_curate.rebuild_curated(conn)` (imported as `from infn_jobs.store.export import curate as store_curate`).
    3. Log `logger.info("Curated tables rebuilt.")`.
  - Do not copy or re-implement the SQL filter. All employment-like filter logic lives in `store/export/curate.py` (Step 6).
  - Module-level logger: `logger = logging.getLogger(__name__)`.
  - Imports: `import logging`, `import sqlite3` from stdlib; `from infn_jobs.store.export import curate as store_curate`.
  - Per dependency rule: `pipeline` may import from `store` and `config`. It must NOT import from `cli`.

[ ] done

**Substep 7.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 7.2 `pipeline/sync.py` — `run_sync()` main loop

### 7.2.1 Create `src/infn_jobs/pipeline/sync.py`
- **File:** `src/infn_jobs/pipeline/sync.py`
- **Action:** Create
- **Write:**
  ```python
  def run_sync(
      conn: sqlite3.Connection,
      dry_run: bool = False,
      force_refetch: bool = False,
  ) -> None:
      """Full idempotent sync pipeline: fetch all calls → extract PDFs → store."""
  ```
- **Test:** (manual verification — `python3 -c "from infn_jobs.pipeline.sync import run_sync; print('pipeline sync OK')"` prints `pipeline sync OK` with no import error)
- **Notes:**
  - **Imports required:**
    - stdlib: `import logging`, `import sqlite3`
    - config: `from infn_jobs.config.settings import TIPOS, PDF_CACHE_DIR, init_data_dirs`
    - fetch: `from infn_jobs.fetch.client import get_session`
    - fetch: `from infn_jobs.fetch.orchestrator import fetch_all_calls`
    - extract: `from infn_jobs.extract.pdf.downloader import download`
    - extract: `from infn_jobs.extract.pdf.mutool import extract_text`
    - extract: `from infn_jobs.extract.parse.row_builder import build_rows`
    - store: `from infn_jobs.store.upsert import upsert_call, upsert_position_rows`
    - domain: `from infn_jobs.domain.position import PositionRow`
  - Module-level logger: `logger = logging.getLogger(__name__)`.
  - **Algorithm — full body of `run_sync()`:**
    1. Call `init_data_dirs()` — ensures `data/pdf_cache/` and `data/exports/` exist before any I/O.
    2. Create one HTTP session: `session = get_session()`.
    3. For each `tipo` in `TIPOS`:
       - Log: `logger.info("Fetching tipo %s (active + expired)", tipo)`.
       - `calls = fetch_all_calls(session, tipo)` — returns `list[CallRaw]` with `listing_status` and `source_tipo` already set by the orchestrator.
       - For each `call` in `calls`:
         - Log: `logger.info("Processing detail_id=%s", call.detail_id)`.
         - Initialise: `rows: list[PositionRow] = []`.
         - Resolve `anno`: `anno = int(call.anno) if call.anno and call.anno.isdigit() else None`.
         - Determine dest path: `dest = PDF_CACHE_DIR / f"{call.detail_id}.pdf"`.
         - **PDF branch:**
           - If `call.pdf_url is None`:
             - `call.pdf_fetch_status = "skipped"`.
             - Log: `logger.info("PDF %s: skipped (no url)", call.detail_id)`.
           - Else:
             - `pdf_path = download(call.pdf_url, dest, force=force_refetch)`.
             - If `pdf_path is None`:
               - `call.pdf_fetch_status = "download_error"`.
               - Log: `logger.info("PDF %s: download_error", call.detail_id)`.
             - Else (download succeeded or file was cached):
               - Log: `logger.info("PDF %s: downloaded", call.detail_id)`.
               - Try `text, text_quality = extract_text(pdf_path)`.
               - On `RuntimeError`:
                 - `call.pdf_fetch_status = "parse_error"`.
                 - Log: `logger.info("PDF %s: parse_error", call.detail_id)`.
               - On success:
                 - `rows, pdf_call_title = build_rows(text, call.detail_id, text_quality, anno)`.
                 - `call.pdf_call_title = pdf_call_title`.
                 - `call.pdf_cache_path = str(dest)`.
                 - `call.pdf_fetch_status = "ok"`.
                 - Log: `logger.info("detail_id=%s: %d position_rows built", call.detail_id, len(rows))`.
                 - Log: `logger.info("PDF %s: ok", call.detail_id)`.
         - **Upsert branch:**
           - If `dry_run`:
             - Log: `logger.info("dry_run=True: skipping DB writes for detail_id=%s", call.detail_id)`.
           - Else:
             - `upsert_call(conn, call)`.
             - If `rows`: `upsert_position_rows(conn, rows)`.
  - **Critical — `build_rows` return contract:** `build_rows` returns `tuple[list[PositionRow], str | None]`. The second element is `pdf_call_title` (call-level). Per CLAUDE.md: "The pipeline (`run_sync`) unpacks it, sets `call.pdf_call_title`, then calls `upsert_call`. Never store `pdf_call_title` inside `PositionRow`." This must happen **before** `upsert_call`, not after.
  - **`download()` is cache-aware:** if `dest` already exists and `force_refetch=False`, `download()` returns `dest` without re-downloading. The pipeline always calls `extract_text()` on the returned path. Do NOT skip text extraction for cached PDFs — the text may not have been extracted in a previous session that crashed.
  - **Empty rows are not failures:** `build_rows()` may return `[]` when `text_quality` is `"no_text"` or `"ocr_degraded"`. Do not crash; just skip `upsert_position_rows` for that call (the `if rows:` guard handles this).
  - **`anno` conversion:** `call.anno` is `str | None`. Use `.isdigit()` to guard conversion before calling `int()`. If `call.anno` is `None` or non-numeric, pass `anno=None` to `build_rows` — it is nullable.
  - **`call.detail_id` is the FK anchor.** Both `upsert_call` and `upsert_position_rows` rely on it. `fetch_all_calls` guarantees `detail_id` is set (parsed from the detail page URL `?id=`). If a call somehow has `detail_id=None`, `upsert_call` will raise a DB constraint error — this is intentional and expected to surface immediately.
  - **`dry_run=True`:** all fetch, download, and extract operations still run. Only the `upsert_call` and `upsert_position_rows` calls are skipped. This allows verifying parsing output without writing to the DB.
  - **Rate limiting:** enforced inside `fetch_all_calls` and `download` (both call `time.sleep(RATE_LIMIT_SLEEP)` between requests). `run_sync` does not add additional sleeps.

[ ] done

**Substep 7.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 7.3 Sync loop: PDF handling and `build_rows` → `pdf_call_title` verification

Note: the implementation for this substep is written in 7.2.1. This substep is a verification gate
for the most critical data-flow path in the pipeline: correct `pdf_fetch_status` assignment and
correct unpacking of the `build_rows` tuple to set `call.pdf_call_title` before upsert.

### 7.3.1 Verify PDF handling flow and `build_rows` → `pdf_call_title` pipeline
- **File:** `src/infn_jobs/pipeline/sync.py`
- **Action:** (verification — no code change; implementation written in 7.2.1)
- **Write:** (no new code — confirm the following invariants are present in `run_sync()`)
- **Test:** (manual verification — inspect `src/infn_jobs/pipeline/sync.py` and confirm:
  1. `call.pdf_fetch_status = "skipped"` is set before any upsert when `call.pdf_url is None`.
  2. `call.pdf_fetch_status = "download_error"` is set when `download()` returns `None`.
  3. `call.pdf_fetch_status = "parse_error"` is set when `extract_text()` raises `RuntimeError`.
  4. `call.pdf_fetch_status = "ok"` is set on the success path only.
  5. The `build_rows` return value is unpacked as `rows, pdf_call_title = build_rows(...)`.
  6. `call.pdf_call_title = pdf_call_title` appears **before** `upsert_call(conn, call)`.
  7. `call.pdf_cache_path = str(dest)` is set on the success path.
  8. `upsert_position_rows` is guarded by `if rows:` — not called on empty list.
  9. `init_data_dirs()` is called at the top of `run_sync()`, before the tipo loop.)
- **Notes:**
  - The ordering of steps 5 and 6 is not negotiable: `upsert_call` must see the populated `call.pdf_call_title` to persist it. If `upsert_call` is called before `pdf_call_title` is set, the DB row will store `NULL` for `pdf_call_title` on every sync, losing the extracted title.
  - The `dest` path (`PDF_CACHE_DIR / f"{call.detail_id}.pdf"`) is used for both `download(…, dest)` and `call.pdf_cache_path = str(dest)`. Both must reference the same `dest` object to stay consistent.
  - `pdf_fetch_status` is set unconditionally for every branch — it must never remain `None` after `run_sync` processes a call. If a new branch is added later (e.g., format not supported), it must set `pdf_fetch_status` before upsert.

[ ] done

**Substep 7.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 7.4 Progress logging

Note: the logging calls are implemented in 7.2.1. This substep verifies that the log output
at INFO level matches the standard defined in CLAUDE.md.

### 7.4.1 Verify progress logging output in `run_sync()`
- **File:** `src/infn_jobs/pipeline/sync.py`
- **Action:** (verification — no code change; logging calls written in 7.2.1)
- **Write:** (no new code — confirm the following log calls exist in `run_sync()`)
- **Test:** (manual verification — run `python3 -c "import logging; logging.basicConfig(level=logging.INFO); import sqlite3; from infn_jobs.pipeline.sync import run_sync"` and confirm no import errors; then review the source of `sync.py` and confirm each required log statement is present at the correct level)
- **Notes:**
  - Required INFO log messages per CLAUDE.md Logging Standard:
    - Per-tipo: `logger.info("Fetching tipo %s (active + expired)", tipo)` — emitted once per tipo before `fetch_all_calls`.
    - Per-call: `logger.info("Processing detail_id=%s", call.detail_id)` — emitted once per call, before the PDF branch.
    - PDF download outcome (one of):
      - `logger.info("PDF %s: skipped (no url)", call.detail_id)` — when `pdf_url is None`.
      - `logger.info("PDF %s: downloaded", call.detail_id)` — when `download()` returns a path.
      - `logger.info("PDF %s: download_error", call.detail_id)` — when `download()` returns `None`.
    - PDF extract outcome (one of, on the download-success path):
      - `logger.info("PDF %s: parse_error", call.detail_id)` — when `extract_text()` raises.
      - `logger.info("PDF %s: ok", call.detail_id)` — on full success.
    - Rows built (on the extract-success path): `logger.info("detail_id=%s: %d position_rows built", call.detail_id, len(rows))`.
    - Dry run: `logger.info("dry_run=True: skipping DB writes for detail_id=%s", call.detail_id)` — when `dry_run=True`.
  - Use `%s` / `%d` style (lazy formatting) throughout — never f-strings in `logger.*()` calls. This avoids formatting cost when the log level is suppressed.
  - DEBUG-level logging for internal parsing steps lives in the extract layer modules (`mutool.py`, `row_builder.py`, etc.) — do not duplicate it here.
  - The `rebuild_curated()` wrapper in `pipeline/curate.py` has its own INFO log calls (7.1.1). `run_sync()` does NOT call `rebuild_curated()` — that is invoked separately by the CLI command `export-csv` (Step 8). Do not call it inside the sync loop.

[ ] done

**Substep 7.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## Verification

```bash
pytest tests/ -v
ruff check src/infn_jobs/pipeline/
```

Expected: all existing tests green (pipeline adds no new test files), ruff exits 0.

Manual checks:
- `python3 -c "from infn_jobs.pipeline.curate import rebuild_curated; from infn_jobs.pipeline.sync import run_sync; print('pipeline OK')"` prints `pipeline OK`.
- Inspect `src/infn_jobs/pipeline/sync.py` — confirm `call.pdf_call_title = pdf_call_title` appears before `upsert_call(conn, call)` on the success path.
- Inspect `src/infn_jobs/pipeline/sync.py` — confirm `init_data_dirs()` is the first call inside `run_sync()`.
- Inspect `src/infn_jobs/pipeline/sync.py` — confirm `if rows:` guards `upsert_position_rows` on every code path.
- Run `ruff check src/infn_jobs/pipeline/sync.py` — zero errors (especially check import order: isort rule `I`).
