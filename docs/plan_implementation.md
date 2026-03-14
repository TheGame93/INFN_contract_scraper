# INFN Jobs Scraper — Implementation Plan

> **Location:** `docs/plan_implementation.md`
> **See also:** [Desiderata](plan_desiderata.md) · [Functions Index](info_functions.md)

---

## Design Principles

- **Each file does one thing.** No file mixes I/O with parsing, no file mixes schema with queries.
- **Dependency direction:** `domain` has no dependencies. `fetch`, `extract`, `store` depend on `domain` and `config`. `pipeline` depends on all infrastructure layers. `cli` depends only on `pipeline`.
- **Store schema/projections are spec-driven.** `store/spec/` is the single source of truth for ordered table columns and view projections; store SQL wiring consumes these specs.
- **New sections = primarily new files.** Adding a new INFN source type means new files under `fetch/` and `extract/parse/fields/`. Schema extensions (`store/schema.py`) and CLI registration (`cli/main.py`) are the only expected edit points.

---

## Source File Tree (~30 files)

```
src/infn_jobs/
│
├── __main__.py                      # python3 -m infn_jobs → cli.main
│
├── cli/
│   ├── __init__.py
│   ├── main.py                      # build_parser(), dispatch to commands
│   ├── cmd_sync.py                  # execute(args) → pipeline.sync
│   └── cmd_export.py                # execute(args) → pipeline.export
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # BASE_URL, TIPOS (5 types), DB_PATH, EXPORT_DIR, PDF_CACHE_DIR
│
├── domain/
│   ├── __init__.py
│   ├── call.py                      # @dataclass CallRaw (listing + detail fields, all nullable)
│   ├── position.py                  # @dataclass PositionRow (one contract line from PDF)
│   └── enums.py                     # ListingStatus, ContractType, ParseConfidence, TextQuality
│
├── fetch/
│   ├── __init__.py
│   ├── client.py                    # requests.Session with retry, rate-limit, user-agent
│   ├── listing/
│   │   ├── __init__.py
│   │   ├── url_builder.py           # build_urls(tipo) -> list[str] (active + expired)
│   │   └── parser.py                # parse_rows(html) -> list[dict]
│   ├── detail/
│   │   ├── __init__.py
│   │   └── parser.py                # parse_detail(html, detail_id) -> CallRaw  (all fields nullable)
│   └── orchestrator.py              # fetch_all_calls(session, tipo) -> list[CallRaw]
│                                    #   builds active + expired URLs, calls parse_rows() for each,
│                                    #   fetches each detail + parse_detail(), sets listing_status
│                                    #   on each CallRaw from the URL variant (active/expired) used
│                                    #   NOTE: assumes single-page listings (no pagination observed).
│                                    #   If any tipo returns 0 rows, check for pagination params
│                                    #   and update url_builder.py. Document in known_edge_cases.md.
│
├── extract/
│   ├── __init__.py
│   ├── pdf/
│   │   ├── __init__.py
│   │   ├── downloader.py            # download(url, dest) -> Path  (cache-aware, returns None if no url)
│   │   └── mutool.py                # extract_text(pdf_path) -> tuple[str, TextQuality]
│   └── parse/
│       ├── __init__.py
│       ├── segmenter.py             # segment(text) -> list[str]  (split multi-entry PDFs)
│       ├── row_builder.py           # build_rows(text, detail_id, text_quality, anno) -> tuple[list[PositionRow], str | None]
│       │                            #   second element is pdf_call_title (call-level); pipeline sets it on CallRaw before upsert
│       ├── fields/
│       │   ├── __init__.py
│       │   ├── contract_type.py     # extract contract_type + contract_subtype (era-aware)
│       │   ├── duration.py          # extract duration_months + duration_raw (era label variants)
│       │   ├── income.py            # extract all 7 EUR income/cost fields (era label variants)
│       │   ├── metadata.py          # extract pdf_call_title, section_structure_department
│       │   └── confidence.py        # score_confidence(row) -> ParseConfidence
│       ├── diagnostics/
│       │   ├── collector.py         # deterministic winner/rejected event collection
│       │   ├── events.py            # ParseEvent model
│       │   ├── render.py            # deterministic diagnostics text rendering
│       │   ├── review_mode.py       # build/render deterministic per-case parse review artifacts
│       │   └── review_mode_helpers.py # internal helpers for review-mode event/evidence assembly
│       ├── core/
│       │   ├── models.py            # ParseRequest/ParseResult and preprocess/segment models
│       │   ├── preprocess.py        # deterministic text normalization with line mapping
│       │   ├── segmentation.py      # deterministic segment boundaries
│       │   ├── classification.py    # weighted contract-family prediction
│       │   ├── execution_shared.py  # shared runtime/review segment execution internals
│       │   └── orchestrator.py      # run_parse_pipeline(request) -> ParseResult
│       ├── rules/
│       │   ├── models.py            # RuleDefinition/RuleContext/ExecutionResult
│       │   ├── executor.py          # deterministic rule execution and rejection trace
│       │   ├── contract_identity.py # rule-driven contract/subtype resolution
│       │   ├── contract_identity_matching.py # internal profile matching helpers
│       │   ├── contract_identity_rule_builders.py # internal contract-identity rule builders
│       │   ├── duration.py          # rule-driven duration resolution
│       │   ├── duration_helpers.py  # duration text-matching helpers
│       │   ├── duration_rule_builders.py # internal duration rule builders
│       │   ├── income.py            # rule-driven income resolution
│       │   ├── income_helpers.py    # income text/amount helper extractors
│       │   ├── income_rule_specs.py # declarative income-field rule specs
│       │   ├── income_resolution_helpers.py # internal income-resolution helpers
│       │   └── section.py           # rule-driven section resolution
│       └── normalize/
│           ├── __init__.py
│           ├── currency.py          # normalize_eur(s) -> float | None
│           ├── dates.py             # parse_date(s) -> date | None  (DD-MM-YYYY)
│           └── subtypes.py          # normalize_subtype(s, anno) -> str | None
│                                    #   Fascia II → Fascia 2
│                                    #   Tipo A / Tipo B (post-2010 only; pre-2010 → NULL)
│
├── store/
│   ├── __init__.py
│   ├── schema.py                    # init_db(conn) — CREATE TABLE IF NOT EXISTS x4
│   ├── upsert.py                    # upsert_call(), upsert_position_rows()
│   ├── spec/
│   │   ├── calls_raw.py             # calls_raw/calls_curated ordered column specs
│   │   ├── position_rows.py         # position_rows ordered column specs
│   │   ├── position_rows_curated.py # position_rows_curated view projection spec
│   │   ├── sql_parts.py             # deterministic SQL/projection fragment renderers
│   │   └── types.py                 # dataclasses: ColumnSpec/TableSpec/ViewSpec
│   └── export/
│       ├── __init__.py
│       ├── curate.py                # SQL for curated filtering + rebuild_curated(conn)
│       └── csv_writer.py            # export_all(conn, export_dir) — writes 4 CSVs
│
└── pipeline/
    ├── __init__.py
    ├── sync.py                      # run_sync(conn, source, limit_per_tipo, download_only, dry_run, force_refetch)
    │                                #   source=local|remote|auto; default local consumes DB/cache
    └── export.py                    # run_export(conn, export_dir) — rebuild curated tables + write 4 CSVs
```

---

## Runtime Request Policy

- Request flow is intentionally single-threaded in v1: no parallel listing/detail/PDF fetches.
- Request pacing uses a 2.5 s target with random jitter (2.0-3.0 s), applied in fetch orchestrator and PDF downloader.
- Retry policy remains in `fetch/client.py`: max 3 retries with exponential backoff for 5xx/connection errors; no generic 4xx retries.
- When pressure signals (`429`, `503`, timeouts) are detected, fetch/downloader log actionable guidance to temporarily increase delay to 5-10 s for the next run.

---

## Test File Tree (~20 files)

```
tests/
├── conftest.py                      # shared: tmp DB, HTTP mock session, fixture loaders
├── fixtures/
│   ├── html/
│   │   ├── listing_active.html
│   │   ├── listing_expired.html
│   │   ├── detail_page_full.html           # all fields present
│   │   └── detail_page_old.html            # missing Numero posti, no PDF link
│   └── pdf_text/
│       ├── single_contract.txt             # digital PDF, full fields
│       ├── missing_fields.txt              # financial fields absent (old record)
│       ├── multi_same_type.txt             # multiple entries, same contract_type
│       ├── multi_mixed_type.txt            # multiple entries, mixed types/subtypes
│       ├── multi_mixed_department.txt      # multiple entries, different section per row
│       ├── ocr_clean.txt                   # scanned, readable
│       ├── ocr_degraded.txt                # scanned, garbled output
│       ├── assegno_tipo_ab.txt             # Assegno di ricerca post-2010 (Tipo A + Tipo B)
│       └── assegno_old.txt                 # Assegno di ricerca pre-2010 (no subtype)
│
├── fetch/
│   ├── test_url_builder.py
│   ├── test_listing_parser.py
│   └── test_detail_parser.py               # includes old-format page (missing fields)
│
├── extract/
│   ├── test_mutool.py                      # mock subprocess; verify text + TextQuality output
│   ├── test_segmenter.py                   # split logic for 1 / N entries
│   ├── fields/
│   │   ├── test_contract_type.py           # includes Assegno Tipo A/B, pre-2010 → NULL
│   │   ├── test_duration.py                # era label variants
│   │   └── test_income.py                  # era label variants (Compenso/Importo/Reddito lordo)
│   └── normalize/
│       ├── test_currency.py                # Italian EUR format variants
│       ├── test_dates.py
│       └── test_subtypes.py                # Fascia II→2, Tipo A/B era-gating, pre-2010 → NULL
│
├── store/
│   ├── test_schema.py                      # tables created, idempotent init
│   ├── test_upsert.py                      # upsert deduplication, first_seen_at immutability
│   └── test_curate.py                      # rebuild_curated: employment rows kept, prize-only excluded
│
└── e2e/
    └── test_sync.py                        # full pipeline, idempotency, row count > call count
```

---

## Layer Responsibilities

| Layer | What it knows | What it must NOT know |
|---|---|---|
| `domain/` | Data shapes, enums | HTTP, DB, filesystem |
| `config/` | Paths, URLs, constants | Business logic |
| `fetch/` | HTTP + HTML → domain objects | DB, PDF parsing |
| `extract/` | PDF bytes → domain objects | HTTP, DB |
| `store/` | Domain objects → SQLite + CSV | HTTP, PDF |
| `pipeline/` | Orchestration order | Transport details | _(no unit tests — covered by e2e Step 9)_ |
| `cli/` | User args → pipeline calls | All internals |

---

## CLI Entry Points

| Command | File | What it does |
|---|---|---|
| `python3 -m infn_jobs sync` | `cli/cmd_sync.py` | Default `source=local`: parse/store using existing `calls_raw` metadata and local cache |
| `python3 -m infn_jobs sync --source remote` | same | Bootstrap/full remote pipeline: fetch → cache/download → parse → store |
| `python3 -m infn_jobs sync --source remote --dry-run` | same | Fetch + parse but skip DB writes |
| `python3 -m infn_jobs sync --source remote --force-refetch` | same | Remote sync and re-download PDFs even if cached |
| `python3 -m infn_jobs sync --source remote --download-only` | same | Fetch calls and materialize cache only; skip parse/store |
| `python3 -m infn_jobs sync --source remote --limit-per-tipo N` | same | Debug partial remote discovery (first `N` calls per tipo) |
| `python3 -m infn_jobs sync --source auto` | same | Local-first mode with remote fallback when `calls_raw` is empty |
| `python3 -m infn_jobs export-csv` | `cli/cmd_export.py` | Rebuild curated tables → write 4 CSV files (via `pipeline.export`) |

Guardrails: local mode bootstrap guidance is `Run sync with --source remote first.`; `--download-only` and `--force-refetch` are invalid with `--source local`.

---

## DB Schema

### `calls_raw`

One row per `detail_id`. All fields except `detail_id` are nullable (older records may omit any of them).
Ordered columns are defined once in `store/spec/calls_raw.py` and consumed by schema/upsert/read/export paths.

```sql
calls_raw (
  detail_id         TEXT PRIMARY KEY,
  source_tipo       TEXT,
  listing_status    TEXT,             -- "active" | "expired"
  numero            TEXT,
  anno              TEXT,
  titolo            TEXT,
  pdf_call_title    TEXT,             -- extracted from PDF body (nullable); fallback for call_title in CSV
  numero_posti_html INTEGER,          -- from HTML detail page
  data_bando        TEXT,
  data_scadenza     TEXT,
  detail_url        TEXT,
  pdf_url           TEXT,             -- NULL if no PDF link on page
  pdf_cache_path    TEXT,             -- NULL if skipped
  pdf_fetch_status  TEXT,             -- "ok" | "download_error" | "parse_error" | "skipped"
  first_seen_at     TEXT,             -- set on first insert, never updated
  last_synced_at    TEXT              -- updated every sync
)
```

### `position_rows`

One-to-many: each row is one contract entry extracted from a PDF.
Ordered columns are defined once in `store/spec/position_rows.py` and consumed by schema/upsert/read/export paths.
`upsert_position_rows(conn, rows)` expects a homogeneous batch (all rows share the same `detail_id`) and validates this before `DELETE`/`INSERT`.

```sql
position_rows (
  detail_id                     TEXT,
  position_row_index            INTEGER,
  -- PDF source quality:
  text_quality                  TEXT,    -- "digital" | "ocr_clean" | "ocr_degraded" | "no_text"
  -- extracted fields (all nullable):
  contract_type                 TEXT,
  contract_type_raw             TEXT,    -- original contract-type text as found in PDF
  contract_subtype              TEXT,    -- canonical: "Fascia 2", "Tipo A", "Tipo B"
  contract_subtype_raw          TEXT,    -- original text as found in PDF
  duration_months               INTEGER,
  duration_raw                  TEXT,
  section_structure_department  TEXT,    -- row-level; may differ across rows of same detail_id
  institute_cost_total_eur      REAL,
  institute_cost_yearly_eur     REAL,
  gross_income_total_eur        REAL,
  gross_income_yearly_eur       REAL,
  net_income_total_eur          REAL,
  net_income_yearly_eur         REAL,
  net_income_monthly_eur        REAL,
  -- evidence snippets (one per extracted field):
  contract_type_evidence        TEXT,
  contract_subtype_evidence     TEXT,
  duration_evidence             TEXT,
  section_evidence              TEXT,
  institute_cost_evidence       TEXT,
  gross_income_evidence         TEXT,
  net_income_evidence           TEXT,
  -- quality:
  parse_confidence              TEXT,    -- "high" | "medium" | "low" (behavioral only)
  PRIMARY KEY (detail_id, position_row_index),
  FOREIGN KEY (detail_id) REFERENCES calls_raw(detail_id)
)
```

### `calls_curated`

Same schema as `calls_raw`. Populated by `rebuild_curated(conn)` using the employment-like filter (keep borsa, incarico di ricerca, incarico post-doc, contratto di ricerca, assegno di ricerca; exclude prize-only notices).

### `position_rows_curated`

**Denormalized analytical VIEW** joining `position_rows` with `calls_curated`. This is the flat table described in `plan_desiderata.md` "Canonical Fields in `position_rows_curated`".
Projection order and expressions are defined once in `store/spec/position_rows_curated.py`.

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

The `call_title` column is a derived field (`COALESCE(pdf_call_title, titolo)`). It exists only in the VIEW and in CSV exports — not stored as a separate DB column.

### Field-Change Workflow

When adding/removing persistence fields:
1. Edit `store/spec/*` definitions first (single source of truth).
2. Align domain dataclasses and assembly/read paths as needed.
3. Update/extend drift guards (`tests/store/test_specs.py`, `tests/store/test_specs_consistency.py`, `tests/extract/test_row_builder.py`).
4. Run `pytest tests/ -v` and `ruff check src/`.

---

## Scripts

Development utilities (not part of the installable package). Already present in the repo:

```text
scripts/
├── gen_info_functions.py       # walk src/infn_jobs/, extract docstrings, write docs/info_functions.md
├── check_canary_provenance.py  # validate canary provenance manifest schema + fixture hashes
├── review_parse_case.py        # deterministic manual parse review for one local PDF/detail_id
└── check_parse_file_sizes.py   # enforce parse-file size warn/fail thresholds
```

Run from the project root: `python3 scripts/gen_info_functions.py`.
Re-run at the end of every session that adds, renames, or removes public functions.
Use `python3 scripts/check_parse_file_sizes.py --root src/infn_jobs/extract/parse --warn 150 --fail 250`
to enforce parse-module split policy.

---

## Extensibility — Future Phases

### v1 Design Constraint: Shared Utilities Must Stay Atomic

The following modules are designed to be reusable by future phases (v2 winner scraper, v3 analytics).
They must not import v1-specific logic (no imports from `fetch/listing/`, `fetch/detail/`,
`extract/parse/fields/`, or `pipeline/sync.py`):

| Module | Reusable capability |
|---|---|
| `extract/pdf/mutool.py` | PDF text extraction via mutool |
| `extract/parse/normalize/currency.py` | Italian EUR format → float |
| `extract/parse/normalize/dates.py` | DD-MM-YYYY → date |
| `extract/parse/normalize/subtypes.py` | Era-aware subtype normalization |
| `fetch/client.py` | HTTP session with retry + rate-limit |
| `config/settings.py` | Shared path constants |
| `store/schema.py` | Schema extension point (add tables via `init_db`) |

When implementing v1, keep these modules self-contained: no side effects, no references to
`CallRaw`-specific fields, no hardcoded v1 URLs. v2 will import them directly.

### v2 — Winner Scraper (Delibere)

Scrapes winner announcements from INFN institutional websites (Giunta Esecutiva / Consiglio Direttivo
delibere). Requires account + password + 2FA authentication. May target multiple sites.

New files only — existing v1 files are not modified except `store/schema.py` and `cli/main.py`:

```
fetch/auth/
    __init__.py
    handler.py               # account + password + 2FA session management
                              # credentials from env vars or local secrets file (gitignored)

fetch/delibere/
    __init__.py
    url_builder.py            # build delibere listing URLs (may be multi-site)
    parser.py                 # parse delibere pages → winner records
    navigator.py              # nested navigation (year → session → delibera)

domain/winner.py              # @dataclass WinnerRecord (FK → calls_raw.detail_id)

store/schema.py               ← edit: add winners table
                                (FOREIGN KEY detail_id → calls_raw.detail_id)

pipeline/sync_winners.py      # winner sync orchestration (reuses mutool, normalize/)
cli/cmd_sync_winners.py       # new CLI subcommand
cli/main.py                   ← edit: register sync-winners subcommand
```

### v3 — Analytics

Read-only query modules consuming v1 + v2 data. No changes to scraping pipelines.

```
analytics/
    __init__.py
    positions.py              # v1 position trends (counts, financials, geography, text_quality)
    winners.py                # v2 winner correlation (time-to-fill, fill rates, cross-ref with v1)
```

Analytics consumes the SQLite DB or exported CSVs. Implementation deferred until v1 data quality
is validated.

---

## Verification Checklist

1. `python3 -m infn_jobs sync --source remote` completes without error; DB has rows across all 5 source types.
2. Second `sync` run produces identical row counts (idempotency).
3. `first_seen_at` is unchanged on second run; `last_synced_at` is updated.
4. At least one call has `pdf_fetch_status = skipped` (old record without PDF link).
5. `text_quality` values are present; `ocr_degraded` rows have `parse_confidence = low`. `no_text` PDFs produce 0 `position_rows`.
6. `python3 -m infn_jobs export-csv` writes 4 non-empty CSV files.
7. `position_rows_curated.csv` has `detail_id + position_row_index` on every row.
8. At least one `detail_id` with multiple `position_row_index` values (multi-entry PDF).
9. `pytest tests/ -v` — all unit and e2e tests pass.
