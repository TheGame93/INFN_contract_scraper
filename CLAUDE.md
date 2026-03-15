# CLAUDE.md — Project Context for Claude Code

This file is read automatically by Claude Code at every session start.
It gives Claude the context needed to work on this project without re-explaining everything.

---

## Project

**INFN Jobs Scraper** — a Python CLI tool that scrapes job opportunities from `jobs.dsi.infn.it`,
stores them in SQLite, and exports analytics-ready CSVs.

Goal: analytics on INFN positions (borse, incarichi ricerca, post-doc, contratti di ricerca, assegni di ricerca).
Dataset spans from 2003 to present — **high field variability is the norm**.

**Future phases (design constraints on v1, not implemented yet):**
- **v2 — Winner Scraper:** scrapes "delibere" from INFN institutional websites (Giunta/Direttivo) for winner announcements. Requires account + password + 2FA. Links winners to `calls_raw.detail_id`. See `plan_desiderata.md § Future Phases`.
- **v3 — Analytics:** read-only analysis of v1 position data and v2 winner data (trends, correlations, fill rates).

---

## Docs

All design documents live in `docs/`:

| File | Purpose |
|---|---|
| `docs/plan_desiderata.md` | What to build: fields, rules, test plan, assumptions |
| `docs/plan_implementation.md` | How to build it: file tree, layers, DB schema, extensibility |
| `docs/info_functions.md` | Index of every function and class in the codebase |
| `docs/info_csvfields.md` | Tracking grid for exported CSV field lists and per-field parsing status |
| `docs/step/planning_step.md` | Active step tracker — **read this at every new session** |
| `docs/step/policy_step.md` | Rules for the step system (adding steps, marking done) |
| `docs/known_edge_cases.md` | Specific detail_ids with parser failures or unexpected behavior |

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
│       ├── fields/      → one file per extracted field group
│       ├── core/        → shared parse execution internals (runtime + review mode)
│       ├── diagnostics/ → deterministic review/event artifacts
│       ├── rules/       → deterministic rule execution per field family
│       └── normalize/   → pure conversion functions (currency, dates, subtypes/era-variants)
├── store/        → SQLite schema, upsert, CSV export
│   ├── spec/     → ordered table/view specs (single source of truth for store SQL/projections)
│   └── export/
└── pipeline/     → orchestration only
```

**Dependency rule:** `domain` has no dependencies. Everything else may depend on `domain` and `config`.
`pipeline` is the only layer that wires other layers together.
`cli` only calls `pipeline`.

---

## Key Conventions

- **Docstrings are mandatory.** Every public function, method, and class must have a one-line docstring summarising what it does. Private helpers (`_name`) may omit them if the logic is self-evident.
- **One concern per file.** No file mixes HTTP with parsing, or schema with queries.
- **Store field definitions are spec-driven.** `src/infn_jobs/store/spec/` is the single source of truth for ordered table columns and view projections; `schema`, `upsert`, `read`, and CSV export must consume these specs, not hardcoded lists.
- **All fields are nullable — always.** HTML fields missing on old pages → `NULL`, never a crash. PDF fields not found → `NULL` + `NULL` evidence, never a crash.
- **Upsert by `detail_id`.** Running `sync` twice must produce identical row counts.
- **`upsert_position_rows` input contract:** each call must receive rows for exactly one `detail_id`; mixed-detail batches raise `ValueError` before any SQL write.
- **`detail_id` is the stable FK.** Never delete or rename it — v2 winner tables will reference it.
- **Italian number format:** `33.681,30` normalizes to `33681.30`. See `extract/parse/normalize/currency.py`.
- **Date format:** `DD-MM-YYYY`. See `extract/parse/normalize/dates.py`.
- **Subtype normalization:** always store both canonical and raw values. Key mappings:
  - `Fascia I/II/III` and `Fascia 1/2/3` → canonical `Fascia 1/2/3`
  - `Tipo A` / `Tipo B` (Assegno di ricerca, post-2010 only) → canonical `Junior` / `Senior` (`anno < 2010` or missing `anno` → `NULL`)
- **`text_quality`** classifies the PDF source: `digital | ocr_clean | ocr_degraded | no_text`. Classification policy lives in `extract/pdf/text_quality.py` and is consumed by `extract/pdf/mutool.py`. Determines whether missing financial fields are a parse failure or an expected gap.
- **Temporal variability:** pre-2010 PDFs are often scanned. Label variants for the same field differ across 20+ years of templates. The `normalize/` layer must handle all known variants. Use `anno` in analytics to contextualize NULL financial fields.
- **`parse_confidence` is behavioral only** — it reflects parser success, not data availability. NULL EUR fields in old records do not lower confidence.
- **Character encoding:** always pass `response.content` (bytes) to BeautifulSoup, never `response.text`. Let BeautifulSoup detect encoding from the HTML `<meta charset>` tag. Old pages may be ISO-8859-1.
- **HTTP rate limit:** single-threaded requests only. Use a 2.5 s target delay with random jitter (2.0-3.0 s) between requests. Max 3 retries with exponential backoff on 5xx. Do not retry generic 4xx errors; treat `429`/`503`/timeouts as pressure signals, continue safely, and log guidance to temporarily increase delay to 5-10 s for the next run. User-Agent: `infn-jobs-scraper/1.0 (research-tool)`.
- **PDF URL resolution:** if the href starts with `http`, use as-is. Otherwise join with BASE_URL origin (scheme + host only, not path).
- **SQLite connection lifecycle:** created in the CLI layer, passed as a parameter to `run_sync()`. Each upsert commits immediately (SQLite autocommit per statement). No transaction wraps the full sync — partial runs are safe because every re-run is fully idempotent.
- **`position_row_index`:** 0-based integer, assigned by order of appearance in `segment()` output. Deterministic for identical PDF text. Never reorder — v2 winner tables will use `(detail_id, position_row_index)` as FK.
- **Pipeline row-cardinality reconciliation guard:** after `build_rows()` and before any upsert, `pipeline/row_reconciliation.py` applies a conservative guard. Trigger: `numero_posti_html == 1` and parsed rows > 1 → keep only the single strongest row using deterministic scoring (contract_type, subtype, duration, income, parse_confidence) with lowest `position_row_index` as final tie-break. Missing/invalid `numero_posti_html` → no-op (all rows kept). The retained row preserves its original parser-assigned `position_row_index` (no renumbering). Decision is logged at INFO with `reason`, `raw_rows`, and `kept_rows`.
- **`fetch_all_calls` conversion:** `fetch/orchestrator.py` calls `parse_rows()` to get listing dicts, then for each row calls `parse_detail()` to build `CallRaw`. It sets `listing_status` (`active`/`expired`) from the URL variant used, then returns the assembled `CallRaw` list.
- **`build_rows` return type:** `extract/parse/row_builder.py` returns `tuple[list[PositionRow], str | None]`. The second element is `pdf_call_title` (call-level, from the PDF body). The pipeline (`run_sync`) unpacks it, sets `call.pdf_call_title`, then calls `upsert_call`. Never store `pdf_call_title` inside `PositionRow`.
- **Runtime/review parser parity contract:** `extract/parse/row_builder.py` and `extract/parse/diagnostics/review_mode.py` must both consume shared segment execution internals from `extract/parse/core/execution_shared.py` to avoid drift.
- **Multiline extraction policy:** rule extractors must support adjacent-line label/value splits deterministically (shared helper: `extract/parse/rules/text_windows.py`) and keep stable winner precedence.
- **Sync source modes:** `sync` defaults to `source=local` (reuse `calls_raw` + local cache). First-run bootstrap on empty DB/cache must use `--source remote` ("Run sync with --source remote first.").
- **`--dry-run` semantics:** runs discovery/cache/parse for the selected source mode, then skips all `upsert_*` and `rebuild_curated` calls.
- **Sync guardrails:** `--download-only` and `--force-refetch` are invalid with `--source local`; `--limit-per-tipo` applies to remote discovery flows.
- **`detail_url` construction:** `{BASE_URL}/dettagli_job.php?id={detail_id}`. Built in `fetch/detail/parser.py` and stored on `CallRaw`.
- **Pagination fallback:** listings are assumed single-page (no pagination observed). If any tipo returns 0 rows, investigate for pagination params, update `url_builder.py`, and document in `docs/known_edge_cases.md`.
- **`no_text` PDFs:** `text_quality = no_text` means mutool succeeded but extracted nothing. Set `pdf_fetch_status = ok` (not `parse_error`). Produce 0 `position_rows`. Reserve `parse_error` for actual mutool failures (non-zero exit code).
- **Shared utilities must stay atomic.** Modules in `extract/pdf/`, `extract/parse/normalize/`, and `fetch/client.py` are designed for reuse by v2 (winner scraper). They must not import v1-specific logic (no imports from `fetch/listing/`, `fetch/detail/`, `extract/parse/fields/`, or `pipeline/sync.py`). See `plan_implementation.md § Extensibility`.
- **Field-change workflow:** when adding/removing persistence fields, update `store/spec` first, then align dataclasses/tests (`test_specs.py`, `test_specs_consistency.py`, `test_row_builder.py`) before changing runtime wiring. Regenerate `docs/info_functions.md` when public functions/classes change.
- **CSV structure change rule:** if exported CSV structure changes (fields added/removed/renamed/reordered), update `docs/info_csvfields.md` by adding/removing the corresponding rows in the affected CSV table(s).
- **Parse review workflow:** use `python3 scripts/review_parse_case.py --detail-id <id> --pdf-path <local.pdf> [--anno YYYY]` to emit deterministic segment/rule/evidence artifacts for manual audits.
- **Canary provenance workflow:** use `python3 scripts/check_canary_provenance.py --manifest docs/regressions/canary_provenance.md` to enforce fixture/hash integrity for the contract canary matrix.
- **Parse file-size policy:** keep parse modules near ~150 lines and below the hard ceiling of 250 lines. Enforce with `python3 scripts/check_parse_file_sizes.py --root src/infn_jobs/extract/parse --warn 150 --fail 250`.

---

## Logging Standard

Every module uses `logging.getLogger(__name__)`. No `print()` in library code.

The CLI configures root logging once with:
- one file handler (full INFO stream) writing per-run logs under `data/logs/sync_<timestamp>.log`,
- one terminal handler filtered to warnings/errors plus runtime-status logger records (`infn_jobs.runtime.*`).

Log every significant I/O event at INFO:
- Starting a new tipo (`"Fetching tipo Borsa (active)"`)
- Each detail page fetch (`"Processing detail_id=1234"`)
- PDF download outcome (`"PDF 1234: downloaded"` / `"PDF 1234: skipped (no url)"`)
- pdf_fetch_status result (`"PDF 1234: parse_error"`)
- Rows built (`"detail_id=1234: 3 position_rows built"`)

Runtime sync progress is emitted on `infn_jobs.runtime.sync`:
- start line (`source`, logfile path, heartbeat interval),
- phase completion lines with elapsed seconds for A/B/C/D,
- heartbeat every 250 processed contracts,
- final summary counters with total elapsed seconds.

Use DEBUG for internal parsing steps. Use WARNING for recoverable anomalies (unexpected HTML structure, unexpected field value).

---

## `docs/info_functions.md` — Auto-generated function index

`docs/info_functions.md` is a compact, flat index of every public function and class in the
codebase. Its primary purpose is to give a Claude session an instant mental map of the full API
surface without reading 30 individual source files.

**It is auto-generated — do not edit it by hand.**

Run this whenever functions are added, renamed, or removed:

```bash
python3 scripts/gen_info_functions.py
```

The script walks `src/infn_jobs/`, reads each module's docstrings, and writes the index in this
format (sorted by file path):

```markdown
### `function_name`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/...` |
| **Name** | `name` |
| **Parent** | `ClassName` / `module` |
| **Inputs** | `param1: type`, `param2: type` |
| **Output** | `type` — what it returns |
| **Description** | One-line summary (from docstring). |
```

**At session start:** if `docs/info_functions.md` exists and is current, read it for a quick
overview before diving into source files.

---

## Security & Public Repo

**This repository is public on GitHub.** Before every commit:

- **Never commit** credentials, API keys, tokens, passwords, or local filesystem paths.
- **Never commit** `data/` contents — the DB, PDFs, and CSVs are gitignored and contain scraped data.
- **Never commit** `.claude/settings.local.json` — it is gitignored; it contains machine-local paths
  and is auto-generated by Claude Code when permissions are granted on a new machine (no manual
  recreation needed).
- If you add a new config file or secret at runtime, add it to `.gitignore` before the first commit.

The only Claude Code file that IS tracked is `.claude/commands/` — these are project-level prompts
with no machine-specific content and are safe to publish.

---

## Runtime Requirements

- Python 3.11+
- `mutool` (MuPDF) available on PATH — required for PDF text extraction
- Dependencies: `requests`, `beautifulsoup4`, `lxml`

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip3 install -r pythonrequirements.txt
pip3 install -e ".[dev]"
```

The `[dev]` extras include `pytest` and `ruff`.
`pythonrequirements.txt` lists all runtime and dev dependencies — used by the entrypoint
to verify the venv is complete before running any command.

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
python3 -m infn_jobs sync                                  # default source=local: parse/store from existing calls_raw + cache
python3 -m infn_jobs sync --source remote                  # bootstrap/full remote sync: fetch + download + parse + DB writes
python3 -m infn_jobs sync --source remote --dry-run        # fetch + parse only, no DB writes
python3 -m infn_jobs sync --source remote --force-refetch  # remote sync and re-download PDFs even if cached
python3 -m infn_jobs sync --source remote --download-only  # fetch calls + download/cache PDFs only
python3 -m infn_jobs sync --source remote --limit-per-tipo 20
python3 -m infn_jobs sync --source auto                    # local-first; remote fallback when calls_raw is empty
python3 -m infn_jobs export-csv             # write 4 CSVs to data/exports/
```

---

## Tests

```bash
pytest tests/ -v
```

Fixtures live in `tests/fixtures/html/` and `tests/fixtures/pdf_text/`.
Add a fixture file for every new parsing case before writing the parser.
