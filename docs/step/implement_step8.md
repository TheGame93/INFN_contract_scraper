# Step 8 — CLI Layer

> **Location:** `docs/step/implement_step8.md`
> **Prerequisites:** Step 3 complete, Step 6 complete, Step 7 complete
> **Produces:**
> - `src/infn_jobs/__main__.py`
> - `src/infn_jobs/cli/main.py`
> - `src/infn_jobs/cli/cmd_sync.py`
> - `src/infn_jobs/cli/cmd_export.py`

Note: the CLI layer has **no dedicated unit tests** — not listed in `plan_implementation.md`'s test file
tree and covered by the e2e test in Step 9. All sub-substep verification is therefore manual.
The `cli/__init__.py` was created in Step 1 scaffolding; it is not listed in Produces.

---

## 8.1 `__main__.py` entry point

### 8.1.1 Create `src/infn_jobs/__main__.py`
- **File:** `src/infn_jobs/__main__.py`
- **Action:** Create
- **Write:**
  ```python
  from infn_jobs.cli.main import run

  run()
  ```
- **Test:** (manual verification — `python3 -m infn_jobs --help` exits 0 and prints the program usage without an import error)
- **Notes:**
  - This file is the sole entry point for `python3 -m infn_jobs`. Its entire job is to import and call `run()`.
  - Do not add any logic here — all argument parsing, logging configuration, and dispatch live in `cli/main.py`.
  - The standard `if __name__ == "__main__":` guard is **not** needed in `__main__.py` — Python only executes this file when the package is invoked with `-m`, so it is always `__main__`. Adding the guard is harmless but unnecessary.
  - Per CLAUDE.md dependency rule: `cli` is the only layer that calls `pipeline`. `__main__.py` only calls `cli.main`.

[x] done

**Substep 8.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 8.2 `cli/main.py` — parser and dispatcher

### 8.2.1 Create `src/infn_jobs/cli/main.py`
- **File:** `src/infn_jobs/cli/main.py`
- **Action:** Create
- **Write:**
  ```python
  def build_parser() -> argparse.ArgumentParser: ...
  def run() -> None: ...
  ```
- **Test:** (manual verification — `python3 -m infn_jobs --help` prints subcommand list; `python3 -m infn_jobs sync --help` shows `--dry-run` and `--force-refetch` flags; `python3 -m infn_jobs export-csv --help` shows the export subcommand; all exit 0)
- **Notes:**
  - **Imports:**
    - stdlib: `import argparse`, `import logging`, `import sys`
    - CLI: `from infn_jobs.cli import cmd_sync, cmd_export`
    - config: `from infn_jobs.config.settings import init_data_dirs`
  - **`build_parser()` implementation:**
    - Create `parser = argparse.ArgumentParser(prog="infn_jobs", description="INFN Jobs Scraper — fetch, extract, and store INFN job opportunities.")`.
    - Add subparsers: `subparsers = parser.add_subparsers(dest="command", required=True)`.
    - Register `sync` subcommand:
      - `sync_parser = subparsers.add_parser("sync", help="Fetch and store all INFN job listings.")`.
      - `sync_parser.add_argument("--dry-run", action="store_true", default=False, help="Parse only; skip DB writes.")`.
      - `sync_parser.add_argument("--force-refetch", action="store_true", default=False, help="Re-download all PDFs even if cached.")`.
      - `sync_parser.set_defaults(func=cmd_sync.execute)`.
    - Register `export-csv` subcommand:
      - `export_parser = subparsers.add_parser("export-csv", help="Export DB to 4 CSV files in data/exports/.")`.
      - `export_parser.set_defaults(func=cmd_export.execute)`.
    - Return `parser`.
  - **`run()` implementation:**
    1. Configure logging once: `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")`. Per CLAUDE.md: "The CLI configures the root handler once."
    2. Call `init_data_dirs()` — ensures `data/pdf_cache/` and `data/exports/` exist before any command runs. Per CLAUDE.md: "Called once at CLI startup in Step 8 (`cli/main.py`) before any pipeline runs." This call is idempotent (uses `exist_ok=True` internally), so no harm if `run_sync()` also calls it.
    3. `parser = build_parser()`.
    4. `args = parser.parse_args()`.
    5. Wrap dispatch in try/except:
      ```python
      try:
          args.func(args)
      except Exception as exc:
          logging.error("Fatal error: %s", exc)
          print(f"Error: {exc}", file=sys.stderr)
          sys.exit(1)
      ```
    6. On success, `run()` returns normally — Python process exits 0 by default. Do NOT add an explicit `sys.exit(0)`.
  - **Exit code contract:** `sys.exit(1)` is called only from the `except` block in `run()`. The `execute()` functions in cmd modules must raise an exception (not call `sys.exit` themselves) to signal fatal errors. This centralises all exit-code logic in one place.
  - Module-level logger: `logger = logging.getLogger(__name__)`. The `basicConfig` call in `run()` activates this handler.
  - The `func` attribute set by `set_defaults` is always present when dispatch is reached (argparse enforces `required=True` on subparsers). No `hasattr(args, "func")` guard is needed.

[x] done

**Substep 8.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 8.3 `cli/cmd_sync.py`

### 8.3.1 Create `src/infn_jobs/cli/cmd_sync.py`
- **File:** `src/infn_jobs/cli/cmd_sync.py`
- **Action:** Create
- **Write:**
  ```python
  def execute(args: argparse.Namespace) -> None:
      """Open DB, run full sync pipeline, close DB."""
  ```
- **Test:** (manual verification — `python3 -m infn_jobs sync --dry-run` completes without error; confirm `data/infn_jobs.db` is created; confirm log lines mention at least one tipo; `$?` is 0 after the run)
- **Notes:**
  - **Imports:**
    - stdlib: `import argparse`, `import sqlite3`
    - config: `from infn_jobs.config.settings import DB_PATH`
    - store: `from infn_jobs.store.schema import init_db`
    - pipeline: `from infn_jobs.pipeline.sync import run_sync`
  - **`execute()` implementation:**
    ```python
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        run_sync(conn, dry_run=args.dry_run, force_refetch=args.force_refetch)
    finally:
        conn.close()
    ```
  - Per CLAUDE.md: "SQLite connection lifecycle: created in the CLI layer, passed as a parameter to `run_sync()`."
  - `init_db(conn)` is called before `run_sync()` to ensure all 4 tables exist. It is idempotent (`CREATE TABLE IF NOT EXISTS`) — safe to call on every invocation even if the DB already exists.
  - `conn.close()` in the `finally` block ensures the connection is closed even if `run_sync()` raises. The exception propagates up to `run()` in `cli/main.py`, which catches it and calls `sys.exit(1)`.
  - `args.dry_run` and `args.force_refetch` are set to `False` by `add_argument(default=False)` when not specified. No additional guard needed.
  - Do NOT call `logging.basicConfig` here — it was already called by `run()` in `cli/main.py`. Calling it again after handlers are set has no effect, but is misleading.
  - Do NOT call `sys.exit()` here — let exceptions propagate naturally to the dispatcher.

[x] done

**Substep 8.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 8.4 `cli/cmd_export.py`

### 8.4.1 Create `src/infn_jobs/cli/cmd_export.py`
- **File:** `src/infn_jobs/cli/cmd_export.py`
- **Action:** Create
- **Write:**
  ```python
  def execute(args: argparse.Namespace) -> None:
      """Open DB, rebuild curated tables, export 4 CSVs, close DB."""
  ```
- **Test:** (manual verification — `python3 -m infn_jobs export-csv` completes without error; `ls data/exports/` shows four `.csv` files; `$?` is 0)
- **Notes:**
  - **Imports:**
    - stdlib: `import argparse`, `import sqlite3`
    - config: `from infn_jobs.config.settings import DB_PATH, EXPORT_DIR`
    - store: `from infn_jobs.store.schema import init_db`
    - pipeline: `from infn_jobs.pipeline.export import run_export`
  - **`execute()` implementation:**
    ```python
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        run_export(conn, EXPORT_DIR)
    finally:
        conn.close()
    ```
  - `init_db(conn)` is called for safety — `export-csv` may be run independently of `sync`. If the DB does not yet exist, `sqlite3.connect` creates it and `init_db` creates empty tables. The exported CSVs will be empty but the command will not crash.
  - `run_export(conn, EXPORT_DIR)` is the single pipeline entry point for the export command. It calls `rebuild_curated(conn)` internally (refreshing `calls_curated` from `calls_raw`), then calls `export_all(conn, EXPORT_DIR)` to write 4 CSVs. The `position_rows_curated` VIEW updates automatically when `calls_curated` is refreshed.
  - `EXPORT_DIR` is `data/exports/` (resolved in `config/settings.py`). `export_all` creates it if missing (`export_dir.mkdir(parents=True, exist_ok=True)` is called inside `export_all`). No extra mkdir needed here.
  - `args` is passed as a parameter for consistency with the `execute(args)` contract, even though `export-csv` currently has no flags. Future flags (e.g., `--output-dir`) can be added without changing the dispatch mechanism.
  - Do NOT call `sys.exit()` here — propagate exceptions to `run()`.

[x] done

**Substep 8.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 8.5 Exit codes: 0 on success, 1 on fatal error

Note: the exit code logic is implemented in 8.2.1 (`run()` in `cli/main.py`). This substep is a
verification gate confirming the correct exit codes are produced under success and failure conditions.

### 8.5.1 Verify exit code behaviour
- **File:** `src/infn_jobs/cli/main.py`
- **Action:** (verification — no code change; exit code logic implemented in 8.2.1)
- **Write:** (no new code — confirm the following invariants hold)
- **Test:** (manual verification — run each of the following and check `$?` after each command:
  1. `python3 -m infn_jobs --help` → exits 0.
  2. `python3 -m infn_jobs sync --help` → exits 0.
  3. `python3 -m infn_jobs export-csv --help` → exits 0.
  4. `python3 -m infn_jobs sync --dry-run` → exits 0 (dry-run completes without DB writes).
  5. `python3 -m infn_jobs export-csv` → exits 0 (even if DB is empty — empty CSVs are valid).
  6. Trigger a fatal error — e.g., temporarily rename `data/` to `data_bak/` and run `python3 -m infn_jobs export-csv` → exits 1 and prints `Error: ...` to stderr; restore `data/` afterwards.
  7. `python3 -m infn_jobs unknown_command` → exits 2 (argparse default for unrecognised subcommand) and prints usage to stderr — this is correct and expected; do NOT override argparse's exit code for parse errors.)
- **Notes:**
  - Exit 0 = success. Produced by `run()` returning normally (no `sys.exit(0)` call needed).
  - Exit 1 = fatal runtime error. Produced by `sys.exit(1)` in the `except` block of `run()`.
  - Exit 2 = argparse parse error (unrecognised command / missing required argument). This is argparse's default and is correct — do NOT intercept it.
  - The `execute()` functions in `cmd_sync.py` and `cmd_export.py` must NOT call `sys.exit()`. They propagate exceptions to `run()`, which is the single point of exit-code control.
  - Confirm that `print(f"Error: {exc}", file=sys.stderr)` appears in the `except` block in `run()` — the error message must go to stderr, not stdout, so it does not pollute piped output.
  - Logging (`logger.error(...)`) is also called on the same exception — both the structured log and the human-readable stderr message are emitted. This is intentional: the log line goes to the logger handler; the print goes directly to stderr regardless of log level.

[x] done

**Substep 8.5 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## Verification

```bash
pytest tests/ -v
ruff check src/infn_jobs/cli/
ruff check src/infn_jobs/__main__.py
```

Expected: all existing tests green (CLI adds no new test files), ruff exits 0.

Manual checks:
- `python3 -m infn_jobs --help` — prints usage with `sync` and `export-csv` subcommands listed.
- `python3 -m infn_jobs sync --help` — lists `--dry-run` and `--force-refetch` flags.
- `python3 -m infn_jobs sync --dry-run` — completes; `$?` is 0; log shows "Fetching tipo …" lines for all 5 tipos.
- `python3 -m infn_jobs export-csv` — completes; `$?` is 0; `data/exports/` contains `calls_raw.csv`, `calls_curated.csv`, `position_rows_raw.csv`, `position_rows_curated.csv`. Note: `position_rows_curated.csv` is generated by querying the `position_rows_curated` VIEW.
- `python3 -c "from infn_jobs.cli.main import build_parser, run; from infn_jobs.cli import cmd_sync, cmd_export; print('cli OK')"` — prints `cli OK`.
