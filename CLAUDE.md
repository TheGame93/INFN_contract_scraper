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
