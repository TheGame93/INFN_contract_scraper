# CLAUDE.md — Project Context for Claude Code

This file is read automatically by Claude Code at every session start.
It gives Claude the context needed to work on this project without re-explaining everything.

---

## Project

**INFN Jobs Scraper** — a Python CLI tool that scrapes job opportunities from `jobs.dsi.infn.it`,
stores them in SQLite, and exports analytics-ready CSVs.

Goal: analytics on INFN positions (borse, incarichi ricerca, post-doc, contratti di ricerca, assegni di ricerca).
Dataset spans from 2003 to present — **high field variability is the norm**.
Future v2 will correlate open/closed calls with winner announcements.

---

## Docs

All design documents live in `docs/`:

| File | Purpose |
|---|---|
| `docs/plan_desiderata.md` | What to build: fields, rules, test plan, assumptions |
| `docs/plan_implementation.md` | How to build it: file tree, layers, DB schema, extensibility |
| `docs/info_functions.md` | Index of every function and class in the codebase |
| `docs/step/planning_step.md` | Active step tracker — **read this at every new session** |
| `docs/step/policy_step.md` | Rules for the step system (adding steps, marking done) |

**Session start:** read `docs/step/planning_step.md` → check `## Currently Active` → open the relevant `docs/step/implement_stepN.md` → continue from the first `[ ]` sub-substep.

**Always read the relevant doc before starting work on a subsystem.**

---

## Architecture

```
src/infn_jobs/
├── cli/          → user-facing commands only
├── config/       → constants, paths, URLs
├── domain/       → dataclasses and enums, no I/O
├── fetch/        → HTTP + HTML parsing
│   ├── listing/
│   └── detail/
├── extract/      → PDF → structured data
│   ├── pdf/      → download + mutool + text_quality classification
│   └── parse/
│       ├── fields/    → one file per extracted field group
│       └── normalize/ → pure conversion functions (currency, dates, subtypes/era-variants)
├── store/        → SQLite schema, upsert, CSV export
│   └── export/
└── pipeline/     → orchestration only
```

**Dependency rule:** `domain` has no dependencies. Everything else may depend on `domain` and `config`.
`pipeline` is the only layer that wires other layers together.
`cli` only calls `pipeline`.

---

## Key Conventions

- **One concern per file.** No file mixes HTTP with parsing, or schema with queries.
- **All fields are nullable — always.** HTML fields missing on old pages → `NULL`, never a crash. PDF fields not found → `NULL` + `NULL` evidence, never a crash.
- **Upsert by `detail_id`.** Running `sync` twice must produce identical row counts.
- **`detail_id` is the stable FK.** Never delete or rename it — v2 winner tables will reference it.
- **Italian number format:** `33.681,30` normalizes to `33681.30`. See `extract/parse/normalize/currency.py`.
- **Date format:** `DD-MM-YYYY`. See `extract/parse/normalize/dates.py`.
- **Subtype normalization:** always store both canonical and raw values. Key mappings:
  - `Fascia II` → canonical `Fascia 2`
  - `Tipo A` / `Tipo B` (Assegno di ricerca, post-2010 only; pre-2010 → `NULL`)
- **`text_quality`** classifies the PDF source: `digital | ocr_clean | ocr_degraded | no_text`. Set in `extract/pdf/mutool.py`. Determines whether missing financial fields are a parse failure or an expected gap.
- **Temporal variability:** pre-2010 PDFs are often scanned. Label variants for the same field differ across 20+ years of templates. The `normalize/` layer must handle all known variants. Use `anno` in analytics to contextualize NULL financial fields.
- **`parse_confidence` is behavioral only** — it reflects parser success, not data availability. NULL EUR fields in old records do not lower confidence.
- **Character encoding:** always pass `response.content` (bytes) to BeautifulSoup, never `response.text`. Let BeautifulSoup detect encoding from the HTML `<meta charset>` tag. Old pages may be ISO-8859-1.
- **HTTP rate limit:** 1.0 s sleep between requests. Max 3 retries with exponential backoff on 5xx. User-Agent: `infn-jobs-scraper/1.0 (research-tool)`.
- **PDF URL resolution:** if the href starts with `http`, use as-is. Otherwise join with BASE_URL origin (scheme + host only, not path).
- **SQLite connection lifecycle:** created in the CLI layer, passed as a parameter to `run_sync()`. Each upsert commits immediately (SQLite autocommit per statement). No transaction wraps the full sync — partial runs are safe because every re-run is fully idempotent.
- **`position_row_index`:** 0-based integer, assigned by order of appearance in `segment()` output. Deterministic for identical PDF text. Never reorder — v2 winner tables will use `(detail_id, position_row_index)` as FK.
- **`fetch_all_calls` conversion:** `fetch/orchestrator.py` calls `parse_rows()` to get listing dicts, then for each row calls `parse_detail()` to build `CallRaw`. It sets `listing_status` (`active`/`expired`) from the URL variant used, then returns the assembled `CallRaw` list.

---

## Logging Standard

Every module uses `logging.getLogger(__name__)`. No `print()` in library code.

The CLI configures the root handler once:
```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
```

Log every significant I/O event at INFO:
- Starting a new tipo (`"Fetching tipo Borsa (active)"`)
- Each detail page fetch (`"Processing detail_id=1234"`)
- PDF download outcome (`"PDF 1234: downloaded"` / `"PDF 1234: skipped (no url)"`)
- pdf_fetch_status result (`"PDF 1234: parse_error"`)
- Rows built (`"detail_id=1234: 3 position_rows built"`)

Use DEBUG for internal parsing steps. Use WARNING for recoverable anomalies (unexpected HTML structure, unexpected field value).

---

## Mandatory: Update `docs/info_functions.md`

After every coding session that adds, modifies, or removes a function or class:
1. Open `docs/info_functions.md`.
2. Add/update/remove the corresponding entry.
3. Keep entries sorted by file path.

The index format is:

```markdown
### `function_name`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/...` |
| **Name** | `name` |
| **Parent** | `ClassName` / `module` |
| **Inputs** | `param1: type`, `param2: type` |
| **Output** | `type` — what it returns |
| **Description** | One-line summary. |
```

---

## Runtime Requirements

- Python 3.11+
- `mutool` (MuPDF) available on PATH — required for PDF text extraction
- Dependencies: `requests`, `beautifulsoup4`, `lxml`

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The `[dev]` extras include `pytest` and `ruff`.

### Ruff configuration

Ruff is the linter (replaces flake8 + isort). Config lives in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
# E  — pycodestyle errors (style and syntax)
# F  — pyflakes (undefined names, unused imports)
# I  — isort (import ordering, enforced across all sessions)
# UP — pyupgrade (modernize to Python 3.11 syntax automatically)

[tool.ruff.lint.isort]
known-first-party = ["infn_jobs"]
```

Run before every commit:
```bash
ruff check src/
```

Fix auto-fixable issues:
```bash
ruff check --fix src/
```

---

## CLI

```bash
python -m infn_jobs sync                   # full idempotent pipeline
python -m infn_jobs sync --dry-run         # parse only, no DB writes
python -m infn_jobs sync --force-refetch   # re-download all PDFs even if cached
python -m infn_jobs export-csv             # write 4 CSVs to data/exports/
```

---

## Tests

```bash
pytest tests/ -v
```

Fixtures live in `tests/fixtures/html/` and `tests/fixtures/pdf_text/`.
Add a fixture file for every new parsing case before writing the parser.
