# Step 1 — Project Scaffolding

> **Location:** `docs/step/implement_step1.md`
> **Prerequisites:** (none — first step)
> **Produces:**
> - `pyproject.toml`
> - `.gitignore`
> - `src/infn_jobs/__init__.py`
> - `src/infn_jobs/cli/__init__.py`
> - `src/infn_jobs/config/__init__.py`
> - `src/infn_jobs/domain/__init__.py`
> - `src/infn_jobs/fetch/__init__.py`
> - `src/infn_jobs/fetch/listing/__init__.py`
> - `src/infn_jobs/fetch/detail/__init__.py`
> - `src/infn_jobs/extract/__init__.py`
> - `src/infn_jobs/extract/pdf/__init__.py`
> - `src/infn_jobs/extract/parse/__init__.py`
> - `src/infn_jobs/extract/parse/fields/__init__.py`
> - `src/infn_jobs/extract/parse/normalize/__init__.py`
> - `src/infn_jobs/store/__init__.py`
> - `src/infn_jobs/store/export/__init__.py`
> - `src/infn_jobs/pipeline/__init__.py`
> - `data/pdf_cache/.gitkeep`
> - `data/exports/.gitkeep`
> - `tests/conftest.py`
> - `tests/fixtures/html/.gitkeep`
> - `tests/fixtures/pdf_text/.gitkeep`
> - `tests/fetch/.gitkeep`
> - `tests/extract/.gitkeep`
> - `tests/extract/fields/.gitkeep`
> - `tests/extract/normalize/.gitkeep`
> - `tests/store/.gitkeep`
> - `tests/e2e/.gitkeep`

---

## 1.1 `pyproject.toml` with deps + ruff config + `[dev]` extras

### 1.1.1 Create `pyproject.toml`
- **File:** `pyproject.toml`
- **Action:** Create
- **Write:** (configuration file — no function; contains `[project]` metadata, runtime deps `requests`, `beautifulsoup4`, `lxml`; `[project.optional-dependencies]` dev extras `pytest`, `ruff`; `[tool.setuptools.packages.find]` with `where = ["src"]`; `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.isort]` per CLAUDE.md)
- **Test:** (no isolated test — verified by `pip install -e ".[dev]"` in substep 1.2.1)
- **Notes:** Ruff config per CLAUDE.md: `line-length = 100`, `target-version = "py311"`, `select = ["E", "F", "I", "UP"]`, `known-first-party = ["infn_jobs"]`. Python requires `>=3.11`. Do NOT add a `[project.scripts]` entry yet — `__main__.py` is implemented in Step 8. `src/` layout requires `[tool.setuptools.packages.find] where = ["src"]` and `package-dir = {"" = "src"}` (or equivalent). Discuss ruff config with user before writing if any rule deviates from CLAUDE.md.

[x] done

**Substep 1.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 1.2 Venv setup verification

### 1.2.1 Verify `pip install -e ".[dev]"` succeeds
- **File:** (no file — shell verification)
- **Action:** (no file created)
- **Write:** (no function — manual check)
- **Test:** (manual verification — in the project root: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"` exits 0; then `pytest --version` and `ruff --version` both return version strings; then `python3 -c "import requests; import bs4; import lxml"` returns no error; Windows: use `.venv\Scripts\activate`)
- **Notes:** If `pip install` fails with a build error, check `pyproject.toml` for syntax issues or missing `[build-system]` table. Recommended build backend: `setuptools`. Add `[build-system] requires = ["setuptools>=68"] build-backend = "setuptools.backends.legacy:build"` if not already present.

[x] done

**Substep 1.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 1.3 Package skeleton (`__init__.py` files for all modules)

### 1.3.1 Create `src/infn_jobs/__init__.py`
- **File:** `src/infn_jobs/__init__.py`
- **Action:** Create
- **Write:** (empty file — establishes `infn_jobs` as the root package)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** Keep empty. Do not add version strings, `__all__`, or re-exports here; those belong in later steps if needed.

[x] done

### 1.3.2 Create `src/infn_jobs/cli/__init__.py`
- **File:** `src/infn_jobs/cli/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.3 Create `src/infn_jobs/config/__init__.py`
- **File:** `src/infn_jobs/config/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.4 Create `src/infn_jobs/domain/__init__.py`
- **File:** `src/infn_jobs/domain/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.5 Create `src/infn_jobs/fetch/__init__.py`
- **File:** `src/infn_jobs/fetch/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.6 Create `src/infn_jobs/fetch/listing/__init__.py`
- **File:** `src/infn_jobs/fetch/listing/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.7 Create `src/infn_jobs/fetch/detail/__init__.py`
- **File:** `src/infn_jobs/fetch/detail/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.8 Create `src/infn_jobs/extract/__init__.py`
- **File:** `src/infn_jobs/extract/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.9 Create `src/infn_jobs/extract/pdf/__init__.py`
- **File:** `src/infn_jobs/extract/pdf/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.10 Create `src/infn_jobs/extract/parse/__init__.py`
- **File:** `src/infn_jobs/extract/parse/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.11 Create `src/infn_jobs/extract/parse/fields/__init__.py`
- **File:** `src/infn_jobs/extract/parse/fields/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.12 Create `src/infn_jobs/extract/parse/normalize/__init__.py`
- **File:** `src/infn_jobs/extract/parse/normalize/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.13 Create `src/infn_jobs/store/__init__.py`
- **File:** `src/infn_jobs/store/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.14 Create `src/infn_jobs/store/export/__init__.py`
- **File:** `src/infn_jobs/store/export/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

### 1.3.15 Create `src/infn_jobs/pipeline/__init__.py`
- **File:** `src/infn_jobs/pipeline/__init__.py`
- **Action:** Create
- **Write:** (empty file)
- **Test:** (no isolated test — verified by smoke import in substep 1.6.1)
- **Notes:** (none)

[x] done

**Substep 1.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 1.4 Data directory structure

### 1.4.1 Create `.gitignore`
- **File:** `.gitignore`
- **Action:** Create
- **Write:** (configuration file — no function; must include: `data/`, `!data/pdf_cache/.gitkeep`, `!data/exports/.gitkeep`, `*.pdf`, `*.db`, `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `dist/`, `*.egg-info/`, `.claude/settings.local.json`)
- **Test:** (manual verification — `git status` after adding `data/infn_jobs.db` shows it as untracked/ignored; `git status` shows `data/pdf_cache/.gitkeep` and `data/exports/.gitkeep` as tracked)
- **Notes:** Per CLAUDE.md: `data/` contents are gitignored; `.claude/settings.local.json` is gitignored; `.claude/commands/` is NOT gitignored (tracked). Use negation patterns `!data/pdf_cache/.gitkeep` and `!data/exports/.gitkeep` to allow placeholder files through despite the `data/` rule. If `.gitkeep` negation does not work with the chosen pattern, switch to `data/*.pdf`, `data/*.db`, `data/pdf_cache/*.pdf` instead of blanket `data/`.

[x] done

### 1.4.2 Create `data/pdf_cache/.gitkeep`
- **File:** `data/pdf_cache/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `data/pdf_cache/` is tracked by git so the directory exists after cloning)
- **Test:** (manual verification — `git status` shows this file as tracked and not ignored)
- **Notes:** At runtime, PDF files are downloaded into this directory. They are gitignored. The placeholder ensures the directory exists without committing any scraped data.

[x] done

### 1.4.3 Create `data/exports/.gitkeep`
- **File:** `data/exports/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `data/exports/` is tracked by git)
- **Test:** (manual verification — `git status` shows this file as tracked and not ignored)
- **Notes:** CSV files written at runtime (`calls_raw.csv`, `calls_curated.csv`, `position_rows_raw.csv`, `position_rows_curated.csv`) are gitignored. The placeholder ensures the directory exists after cloning.

[x] done

**Substep 1.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 1.5 Test scaffolding

### 1.5.1 Create `tests/conftest.py`
- **File:** `tests/conftest.py`
- **Action:** Create
- **Write:** (scaffold file — minimal `conftest.py`; a single module-level comment stating that shared fixtures — `tmp_db`, mock HTTP session, fixture loaders — will be added in later steps when the modules they depend on exist)
- **Test:** (no isolated test — verified by `pytest tests/ -v` in substep 1.6.1 returning 0 errors from conftest parsing)
- **Notes:** Keep empty of actual fixtures at this stage. Domain and store layers do not yet exist. The `tmp_db` fixture is added in Step 6 after `store/schema.py` exists. Do not import any `infn_jobs` module from `conftest.py` yet.

[x] done

### 1.5.2 Create `tests/fixtures/html/.gitkeep`
- **File:** `tests/fixtures/html/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/fixtures/html/` exists in git)
- **Test:** (no isolated test — directory existence verified in substep 1.6.1)
- **Notes:** Actual HTML fixtures (`listing_active.html`, `listing_expired.html`, `detail_page_full.html`, `detail_page_old.html`) are created in Step 4 (substep 4.4 and 4.6).

[x] done

### 1.5.3 Create `tests/fixtures/pdf_text/.gitkeep`
- **File:** `tests/fixtures/pdf_text/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/fixtures/pdf_text/` exists in git)
- **Test:** (no isolated test — directory existence verified in substep 1.6.1)
- **Notes:** The 9 PDF text fixture files are created in Step 5 (substep 5.8): `single_contract.txt`, `missing_fields.txt`, `multi_same_type.txt`, `multi_mixed_type.txt`, `multi_mixed_department.txt`, `ocr_clean.txt`, `ocr_degraded.txt`, `assegno_tipo_ab.txt`, `assegno_old.txt`.

[x] done

### 1.5.4 Create `tests/fetch/.gitkeep`
- **File:** `tests/fetch/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/fetch/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_url_builder.py`, `test_listing_parser.py`, `test_detail_parser.py` are created in Step 4.

[x] done

### 1.5.5 Create `tests/extract/.gitkeep`
- **File:** `tests/extract/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/extract/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_mutool.py` and `test_segmenter.py` are created in Step 5.

[x] done

### 1.5.6 Create `tests/extract/fields/.gitkeep`
- **File:** `tests/extract/fields/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/extract/fields/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_contract_type.py`, `test_duration.py`, `test_income.py` are created in Step 5 (substep 5.15).

[x] done

### 1.5.7 Create `tests/extract/normalize/.gitkeep`
- **File:** `tests/extract/normalize/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/extract/normalize/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_currency.py`, `test_dates.py`, `test_subtypes.py` are created in Step 5 (substep 5.7).

[x] done

### 1.5.8 Create `tests/store/.gitkeep`
- **File:** `tests/store/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/store/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_schema.py`, `test_upsert.py`, `test_curate.py` are created in Step 6.

[x] done

### 1.5.9 Create `tests/e2e/.gitkeep`
- **File:** `tests/e2e/.gitkeep`
- **Action:** Create
- **Write:** (empty placeholder file — ensures `tests/e2e/` exists in git)
- **Test:** (no isolated test)
- **Notes:** `test_sync.py` is created in Step 9.

[x] done

**Substep 1.5 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 1.6 Smoke check

### 1.6.1 Verify package imports and ruff clean
- **File:** (no file — shell verification)
- **Action:** (no file created)
- **Write:** (no function — manual check)
- **Test:** (manual verification — with venv activated, run:
  1. `python3 -c "import infn_jobs; import infn_jobs.cli; import infn_jobs.config; import infn_jobs.domain; import infn_jobs.fetch; import infn_jobs.extract; import infn_jobs.store; import infn_jobs.pipeline"` → no `ImportError`
  2. `ruff check src/` → exits 0, zero errors reported
  3. `pytest tests/ -v` → 0 failures, 0 errors (no tests collected is acceptable at this stage))
- **Notes:** If any import fails, confirm the corresponding `__init__.py` file exists under `src/infn_jobs/`. If `ruff` is not found, confirm `pip install -e ".[dev]"` succeeded. The `pytest` run at this stage collects 0 tests; that is expected and correct — the test suite grows in Steps 2–9.

[x] done

**Substep 1.6 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## Verification

```bash
pytest tests/ -v
ruff check src/
```

Expected: all tests green (0 tests collected, 0 errors), ruff exits 0.

Manual checks:
- `python3 -c "import infn_jobs"` returns no error in the activated venv.
- `git status` confirms `data/` PDF/DB files are not tracked; `.gitkeep` placeholders are tracked.
- `git status` confirms `.claude/settings.local.json` is not tracked (gitignored).
