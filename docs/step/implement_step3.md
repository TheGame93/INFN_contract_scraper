# Step 3 — Config Layer

> **Location:** `docs/step/implement_step3.md`
> **Prerequisites:** Step 1 complete
> **Produces:**
> - `src/infn_jobs/config/settings.py`

Note: `plan_implementation.md` lists no test files for the config layer. Constants and path
helpers are verified via manual import checks. The path init helper is verified by running
it against a temp directory.

---

## 3.1 `settings.py` — constants

### 3.1.1 Create `src/infn_jobs/config/settings.py`
- **File:** `src/infn_jobs/config/settings.py`
- **Action:** Create
- **Write:**
  ```python
  BASE_URL: str = "https://jobs.dsi.infn.it"

  TIPOS: list[str] = [
      "Borsa",
      "Incarico di ricerca",
      "Incarico Post-Doc",
      "Contratto di ricerca",
      "Assegno di ricerca",
  ]

  _PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
  DATA_DIR: Path = _PROJECT_ROOT / "data"
  DB_PATH: Path = DATA_DIR / "infn_jobs.db"
  EXPORT_DIR: Path = DATA_DIR / "exports"
  PDF_CACHE_DIR: Path = DATA_DIR / "pdf_cache"

  RATE_LIMIT_SLEEP: float = 1.0
  MAX_RETRIES: int = 3
  USER_AGENT: str = "infn-jobs-scraper/1.0 (research-tool)"
  ```
- **Test:** (manual verification — `python3 -c "from infn_jobs.config.settings import BASE_URL, TIPOS, DB_PATH, EXPORT_DIR, PDF_CACHE_DIR, RATE_LIMIT_SLEEP, MAX_RETRIES, USER_AGENT; assert len(TIPOS) == 5; print(DB_PATH)"` prints the absolute path to `data/infn_jobs.db` with no error)
- **Notes:**
  - `_PROJECT_ROOT` resolves as: `src/infn_jobs/config/settings.py` → parent = `config/` → parent = `infn_jobs/` → parent = `src/` → **this is wrong by one level**. Correct chain: `Path(__file__).parent` = `config/`, `.parent` = `infn_jobs/`, `.parent` = `src/`, `.parent` = project root. So use `Path(__file__).parent.parent.parent.parent` — verify the resolved path prints the expected project root.
  - `TIPOS` values are placeholder strings based on the plan. **Substep 3.3 will verify and correct these** against the live site before Step 4 begins. Do not use them in fetch logic until 3.3.1 is `[x]`.
  - `RATE_LIMIT_SLEEP`, `MAX_RETRIES`, `USER_AGENT` are defined here so `fetch/client.py` (Step 4) can import them without hardcoding values. Per CLAUDE.md: sleep 1.0 s between requests, max 3 retries, User-Agent `infn-jobs-scraper/1.0 (research-tool)`.
  - Config layer has **no imports from other `infn_jobs` modules** — only stdlib (`pathlib`).
  - Do not import `domain` or any other layer here.

[ ] done

**Substep 3.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 3.2 Path initialization helper

### 3.2.1 Add `init_data_dirs()` to `src/infn_jobs/config/settings.py`
- **File:** `src/infn_jobs/config/settings.py`
- **Action:** Edit
- **Write:**
  ```python
  def init_data_dirs() -> None:
      """Create data subdirectories if they do not exist. Idempotent."""
      PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
      EXPORT_DIR.mkdir(parents=True, exist_ok=True)
  ```
- **Test:** (manual verification — `python3 -c "from infn_jobs.config.settings import init_data_dirs; import tempfile; init_data_dirs(); print('ok')"` prints `ok` with no error; run twice to confirm idempotency)
- **Notes:**
  - Uses `mkdir(parents=True, exist_ok=True)` — safe to call multiple times; never raises if directory already exists.
  - Does NOT create `DATA_DIR` itself explicitly — `parents=True` handles the full path.
  - Called once at CLI startup in Step 8 (`cli/main.py`) before any pipeline runs.
  - Does not create `data/infn_jobs.db` — that is created by `store/schema.py` `init_db()` in Step 6.

[ ] done

**Substep 3.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 3.3 Verify TIPOS URL params against live site

### 3.3.1 Verify TIPOS and update `src/infn_jobs/config/settings.py`
- **File:** `src/infn_jobs/config/settings.py`
- **Action:** Edit (only if verified values differ from placeholders)
- **Write:** (update `TIPOS` list with confirmed URL `?tipo=` parameter strings)
- **Test:** (manual verification — open `https://jobs.dsi.infn.it/index.php?tipo=Borsa` in a browser or with `curl`; confirm the page returns listing rows for that tipo; repeat for each of the 5 tipo values; if any value returns zero rows or a 404, find the correct string from the page source and update `TIPOS` accordingly; document any discrepancy in `docs/known_edge_cases.md`)
- **Notes:**
  - Per `plan_desiderata.md`: "the exact string passed to `?tipo=` must be confirmed against the live site."
  - Also verify the `&scad=1` parameter returns expired listings (non-empty results expected for `Borsa&scad=1`).
  - If pagination is observed (a listing returns only a subset of results and shows a "next page" control), document in `docs/known_edge_cases.md` and update `url_builder.py` design in Step 4.
  - **This substep is a hard prerequisite for Step 4.** `build_urls()` and `fetch_all_calls()` consume `TIPOS` directly. If any tipo string is wrong, all calls for that tipo will silently return zero rows.
  - If `settings.py` already has the correct values, mark this done without editing the file.

[ ] done

**Substep 3.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## Verification

```bash
pytest tests/ -v
ruff check src/infn_jobs/config/
```

Expected: all existing tests green, ruff exits 0.

Manual checks:
- `python3 -c "from infn_jobs.config.settings import DB_PATH, PDF_CACHE_DIR, EXPORT_DIR; print(DB_PATH.parent)"` prints the absolute path ending in `data/`.
- `python3 -c "from infn_jobs.config.settings import init_data_dirs; init_data_dirs()"` creates `data/pdf_cache/` and `data/exports/` directories (visible via `ls data/`).
- `python3 -c "from infn_jobs.config.settings import TIPOS; assert len(TIPOS) == 5"` passes — confirming all 5 tipos are present after 3.3.1 verification.
