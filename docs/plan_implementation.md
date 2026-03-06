# INFN Jobs Scraper — Implementation Plan

> **Location:** `docs/plan_implementation.md`
> **See also:** [Desiderata](plan_desiderata.md) · [Functions Index](info_functions.md)

---

## Design Principles

- **Each file does one thing.** No file mixes I/O with parsing, no file mixes schema with queries.
- **Dependency direction:** `domain` ← `pipeline` ← `cli`. Infrastructure (`fetch`, `extract`, `store`) implements domain interfaces.
- **New sections = new files, not edits.** Adding a new INFN source type means new files under `fetch/` and `extract/parse/fields/`, not changes to existing ones.

---

## Source File Tree (~30 files)

```
src/infn_jobs/
│
├── __main__.py                      # python -m infn_jobs → cli.main
│
├── cli/
│   ├── __init__.py
│   ├── main.py                      # build_parser(), dispatch to commands
│   ├── cmd_sync.py                  # execute(args) → pipeline.sync
│   └── cmd_export.py                # execute(args) → store.export
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
│       ├── row_builder.py           # assemble PositionRow from field results + evidence
│       ├── fields/
│       │   ├── __init__.py
│       │   ├── contract_type.py     # extract contract_type + contract_subtype (era-aware)
│       │   ├── duration.py          # extract duration_months + duration_raw (era label variants)
│       │   ├── income.py            # extract all 7 EUR income/cost fields (era label variants)
│       │   ├── metadata.py          # extract pdf_call_title, section_structure_department
│       │   └── confidence.py        # score_confidence(row, text_quality) -> ParseConfidence
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
│   └── export/
│       ├── __init__.py
│       ├── queries.py               # SQL for curated filtering + rebuild_curated(conn)
│       └── csv_writer.py            # export_all(conn, export_dir) — writes 4 CSVs
│
└── pipeline/
    ├── __init__.py
    ├── sync.py                      # run_sync(conn, dry_run, force_refetch) — main orchestrator
    └── curate.py                    # rebuild_curated(conn) — employment-like filter logic
```

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
│   └── test_upsert.py                      # upsert deduplication, first_seen_at immutability
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
| `pipeline/` | Orchestration order | Transport details |
| `cli/` | User args → pipeline calls | All internals |

---

## CLI Entry Points

| Command | File | What it does |
|---|---|---|
| `python -m infn_jobs sync` | `cli/cmd_sync.py` | Full idempotent pipeline: fetch → extract → store |
| `python -m infn_jobs sync --dry-run` | same | Parse but skip DB writes |
| `python -m infn_jobs sync --force-refetch` | same | Re-download all PDFs even if cached |
| `python -m infn_jobs export-csv` | `cli/cmd_export.py` | Read DB → write 4 CSV files |

---

## DB Schema

### `calls_raw`

One row per `detail_id`. All fields except `detail_id` are nullable (older records may omit any of them).

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

```sql
position_rows (
  detail_id                     TEXT,
  position_row_index            INTEGER,
  -- PDF source quality:
  text_quality                  TEXT,    -- "digital" | "ocr_clean" | "ocr_degraded" | "no_text"
  -- extracted fields (all nullable):
  contract_type                 TEXT,
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

`calls_curated` and `position_rows_curated` share the same schemas — populated by the employment-like filter in `pipeline/curate.py`.

The `call_title` column in CSV exports is a derived field: `COALESCE(pdf_call_title, titolo)`. It is not stored as a separate DB column.

---

## Adding New Sections (v2 Extensibility)

Example: winner announcement correlation adds only new files:

```
fetch/winners/
    __init__.py
    url_builder.py
    parser.py

store/schema.py          ← only file touched: add winners table
                           (FOREIGN KEY detail_id → calls_raw)

cli/cmd_sync_winners.py
pipeline/sync_winners.py
```

Zero changes to existing fetch, extract, store, or domain files.

---

## Verification Checklist

1. `python -m infn_jobs sync` completes without error; DB has rows across all 5 source types.
2. Second `sync` run produces identical row counts (idempotency).
3. `first_seen_at` is unchanged on second run; `last_synced_at` is updated.
4. At least one call has `pdf_fetch_status = skipped` (old record without PDF link).
5. `text_quality` values are present; `ocr_degraded` / `no_text` rows have `parse_confidence = low`.
6. `python -m infn_jobs export-csv` writes 4 non-empty CSV files.
7. `position_rows_curated.csv` has `detail_id + position_row_index` on every row.
8. At least one `detail_id` with multiple `position_row_index` values (multi-entry PDF).
9. `pytest tests/ -v` — all unit and e2e tests pass.
