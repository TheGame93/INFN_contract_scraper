# INFN Jobs Scraper — Desiderata

> **Location:** `docs/plan_desiderata.md`
> **See also:** [Implementation Plan](plan_implementation.md) · [Functions Index](info_functions.md)

---

## INFN Jobs Scraper v1 (Python, SQLite, CSV)

### Summary

Build a Python CLI scraper that ingests INFN opportunities from `jobs.dsi.infn.it` for exactly these source types:

- `Borsa`
- `Incarico di ricerca`
- `Incarico Post-Doc`
- `Contratto di ricerca`
- `Assegno di ricerca`

It will scrape both `active` and `expired` listings, backfill full published history, extract structured fields from HTML + PDF, store normalized data in SQLite, and export analytics-ready CSVs.
Status in v1 will expose only source-truth `active/expired` (no inferred `ongoing/closed`).

PDF analytics will support highly variable text and missing values, and will model one-to-many records when a single PDF contains multiple contract lines (including mixed types/subtypes).

---

### Field Variability Over Time

The dataset spans records from 2003 to present. This means **high variability is the norm, not an edge case**. All layers must be designed for it.

#### HTML detail page

- Older records may be missing fields entirely: `Numero posti`, `Bando (PDF)` link, `Data bando`.
- All HTML fields are nullable. A missing field is stored as `NULL` — not a failure.
- If `pdf_url` is absent or empty, set `pdf_fetch_status = skipped`. Do not attempt download.

#### PDF content

- **Pre-2010 records** are often scanned documents. `mutool` may extract degraded or empty text. This is expected.
- A new `text_quality` field classifies the extraction result independently of whether fields were parsed:
  - `digital` — native PDF, clean text extracted
  - `ocr_clean` — scanned but readable text extracted
  - `ocr_degraded` — scanned, garbled output (high noise, low word density)
  - `no_text` — mutool returned nothing or near-nothing
- **Financial amounts were not publicly disclosed in many older bandi.** NULL EUR fields in these records is correct data, not a parsing failure. `parse_confidence` must not penalize it.
- **Label name variants across eras** (not just Italian/English). Examples:
  - Gross income: `Compenso lordo` / `Importo lordo` / `Reddito lordo` / `Retribuzione lorda`
  - Duration: `Durata` / `Periodo` / `per la durata di` / `della durata di`
  - Section: `Sezione di X` / `Sede di X` / just `X`
  - The normalization layer must handle all known variants per era.
- **`Assegno di ricerca` subtype changes with Italian law:**
  - Pre-2010 (L. 449/1997): single type, 1-year renewable. No `Tipo A / B` distinction.
  - Post-2010 (L. 240/2010 Gelmini reform, art. 22): `Tipo A` (junior, 3yr renewable once) and `Tipo B` (senior, 3yr non-renewable). The subtype must be extracted and normalized per era context.

---

### Implementation

#### 1. `fetch`

**HTTP client policy:**
- Sleep 1.0 s between every request (active + expired listings, detail pages, PDF downloads).
- Max 3 retries with exponential backoff on HTTP 5xx or connection error. Fail loudly on 4xx (log + set `pdf_fetch_status = download_error`).
- User-Agent: `infn-jobs-scraper/1.0 (research-tool)`.
- Always pass `response.content` (bytes) to BeautifulSoup — never `response.text`. Let BeautifulSoup detect encoding from the page's `<meta charset>` tag (old pages may be ISO-8859-1).

**Pagination:** assume each listing URL returns all results on a single page (no pagination observed). If a listing returns zero rows, check manually for pagination params and update `url_builder.py` accordingly. Document in `docs/known_edge_cases.md`.

**`tipo` URL parameter values (VERIFY before Step 4):** the exact string passed to `?tipo=` must be confirmed against the live site. Expected values based on site inspection:
- `Borsa`
- `Incarico di ricerca`
- `Incarico Post-Doc`
- `Contratto di ricerca`
- `Assegno di ricerca`
Update `config/settings.py` `TIPOS` dict with verified values before implementing `url_builder.py`.

- Build listing URLs: `index.php?tipo=<...>` and `index.php?tipo=<...>&scad=1`.
- Parse listing table rows (`BANDO`, text, `SCADENZA`, `dettaglio` URL).
- Fetch each `dettagli_job.php?id=...` page and parse:
  - `Numero`, `Anno`, `Titolo`, `Numero posti`, `Tipo`, `Data bando`, `Data scadenza`, `Bando (PDF)`.
  - All fields are nullable — older pages may omit any of them.
- Upsert by `detail_id` (from `dettagli_job.php?id`).
- Set `first_seen_at` only on first insertion; update `last_synced_at` on every sync.
- If `pdf_url` is absent, set `pdf_fetch_status = skipped` immediately.

#### 2. `extract`

**PDF URL resolution:** if the href from the detail page starts with `http`, use as-is. Otherwise join with the BASE_URL origin (scheme + host only, not path). Log the resolved URL at DEBUG before downloading.

**`mutool draw -F txt` output format:** plain text, one block per page, pages separated by a form-feed character (`\x0c`). Column-aligned tables are flattened to space-separated text — no structure is preserved. Scanned pages may include repeated headers/footers and garbled characters. Regex patterns for field extraction must account for mid-word line breaks, extra whitespace, and OCR noise characters.

- **PDF caching:** download PDF to `data/pdf_cache/<detail_id>.pdf`. If the file already exists, skip download. Pass `--force-refetch` to re-download all PDFs.
- Extract text via `mutool draw -F txt`.
- Classify `text_quality` from the extracted text:
  - `no_text` if output is empty or below a minimum character threshold.
  - `ocr_degraded` if the output has a high ratio of non-word characters (garbled OCR).
  - `ocr_clean` if the output is readable but came from a scanned source (heuristic: character-level signals).
  - `digital` otherwise.
- On download or mutool failure: set `pdf_fetch_status` (`ok | download_error | parse_error | skipped`) and continue without crashing. Do not produce `position_rows` for failed calls.
- Build robust normalization for era variants, Italian/English variants, and OCR noise:
  - `Fascia II` / `Fascia 2`, `post-doc` / `postdoc`, `€` formats, line breaks in numbers, garbled characters.
  - Multiple label variants per field across 20+ years of PDF templates (see examples in "Field Variability Over Time").
  - `Assegno di ricerca` subtypes: `Tipo A` / `Tipo B` (post-2010); single type (pre-2010, inferred from `anno`).
- Extract **row-level** fields for each position entry:
  - `section_structure_department` — may differ across rows in the same PDF.
  - `source_contract_type` (if stated in PDF body).
- Extract call-level metadata from PDF when present:
  - `pdf_call_title` (semantic title from bando text).
- Detect and segment multiple contract entries in one PDF:
  - Split by repeated patterns (`n.`, `contratto`, `incarico`, `fascia`, `assegno`, article blocks/tables).
  - Produce `position_rows` with stable `position_row_index`.
  - Allow mixed `contract_type`, `contract_subtype`, and `section_structure_department` across rows.
- For each extracted position row, parse nullable fields:
  - `contract_type`,
  - `contract_subtype` (canonical: `Fascia 2`, `Tipo A`, `Tipo B`, etc.),
  - `contract_subtype_raw` (original text as found in the PDF),
  - `duration_months` (and raw duration text),
  - `institute_cost_total_eur`, `institute_cost_yearly_eur`,
  - `gross_income_total_eur`, `gross_income_yearly_eur`,
  - `net_income_total_eur`, `net_income_yearly_eur`, `net_income_monthly_eur`,
  - `section_structure_department`.
- Keep raw evidence snippets for every parsed field (or `NULL` if missing).
- Normalize EUR numbers from Italian format (`33.681,30` → `33681.30`).

#### 3. `store/export`

- SQLite database `data/infn_jobs.db`.
- Tables:
  - `calls_raw` (one row per `detail_id`, all scraped records),
  - `calls_curated` (employment-like only),
  - `position_rows` (one-to-many extracted contract lines per `detail_id`),
  - `position_rows_curated` (filtered analytical rows).
- Employment-like filter for curated datasets:
  - Keep calls/rows matching: `borsa di studio`, `incarico di ricerca`, `incarico post-doc/postdoc`, `contratto di ricerca`, `assegno di ricerca`.
  - Exclude prize-only/non-employment notices unless linked to an extracted job row.
- CSV exports:
  - `data/exports/calls_raw.csv`
  - `data/exports/calls_curated.csv`
  - `data/exports/position_rows_raw.csv`
  - `data/exports/position_rows_curated.csv`

---

### CLI

- `python -m infn_jobs sync` — full idempotent backfill, active+expired for all 5 types.
- `python -m infn_jobs sync --force-refetch` — re-download all PDFs, even if cached.
- `python -m infn_jobs sync --dry-run` — parse only, no DB writes.
- `python -m infn_jobs export-csv` — write 4 CSVs to `data/exports/`.

---

### Canonical Fields in `position_rows_curated`

#### Linkage / status

| Field | Source |
|---|---|
| `detail_id` | URL param |
| `position_row_index` | assigned during PDF segmentation |
| `source_tipo` | listing URL tipo |
| `listing_status` | `active` or `expired` |

#### Call metadata (from HTML detail page)

| Field | Source |
|---|---|
| `numero` | detail page (nullable) |
| `anno` | detail page (nullable) |
| `numero_posti_html` | detail page `Numero posti` field (nullable) |
| `data_bando` | detail page (nullable) |
| `data_scadenza` | detail page (nullable) |
| `first_seen_at` | set on first insertion, never updated |
| `last_synced_at` | updated every sync |
| `pdf_fetch_status` | `ok \| download_error \| parse_error \| skipped` |

#### Source refs

| Field | Source |
|---|---|
| `detail_url` | constructed from `detail_id` |
| `pdf_url` | parsed from detail page (nullable) |
| `pdf_cache_path` | local path in `data/pdf_cache/` (nullable if skipped) |

#### Analytics fields

| Field | Source |
|---|---|
| `call_title` | prefer `pdf_call_title`; fallback to `titolo` from detail page |
| `section_structure_department` | extracted per row from PDF (nullable) |
| `contract_type` | extracted per row from PDF (nullable) |
| `contract_subtype` | extracted per row — canonical form (e.g. `Fascia 2`, `Tipo A`, `Tipo B`) |
| `contract_subtype_raw` | extracted per row — original text as found in PDF |
| `duration_months` | extracted per row (nullable) |
| `duration_raw` | original text before normalization (nullable) |
| `institute_cost_total_eur` | extracted per row (nullable) |
| `institute_cost_yearly_eur` | extracted per row (nullable) |
| `gross_income_total_eur` | extracted per row (nullable) |
| `gross_income_yearly_eur` | extracted per row (nullable) |
| `net_income_total_eur` | extracted per row (nullable) |
| `net_income_yearly_eur` | extracted per row (nullable) |
| `net_income_monthly_eur` | extracted per row (nullable) |

#### Quality / audit

| Field | Values |
|---|---|
| `*_evidence` | raw text snippet used to extract each field (NULL if field not found) |
| `text_quality` | `digital \| ocr_clean \| ocr_degraded \| no_text` |
| `parse_confidence` | `high \| medium \| low` — behavioral only, see rubric below |

##### `parse_confidence` rubric

Reflects parser behavior, not data availability. NULL financial fields due to era or non-disclosure do not lower confidence.

| Level | Criteria |
|---|---|
| `high` | `duration_months` parsed **and** at least one income field parsed |
| `medium` | `contract_type` parsed, but no financial data found in text |
| `low` | `text_quality` is `ocr_degraded` or `no_text`; or only call metadata parsed from readable text |

---

### Test Plan

#### Unit tests (saved HTML/text fixtures)

- Listing row parsing (active and expired variants).
- Detail page table parsing — full fields present.
- Detail page table parsing — missing `Numero posti`, missing `Bando (PDF)` link (old record).
- EUR normalization: Italian format (`33.681,30`), plain (`1200`), with `€` symbol, line-broken numbers.
- Duration extraction: `12 mesi`, `biennale`, `24 (venti quattro) mesi`, split across lines, era variants (`della durata di 12 mesi`).
- Subtype normalization:
  - `Fascia II` → canonical `Fascia 2`, raw kept.
  - `Tipo A` / `Tipo B` (Assegno di ricerca, post-2010).
  - Pre-2010 Assegno: no subtype present → `contract_subtype = NULL`.
- Label name variants: `Compenso lordo` / `Importo lordo` / `Reddito lordo` all map to gross income.
- OCR noise: garbled characters around numbers, extra whitespace, partial words.

#### PDF extraction tests (text fixtures — mutool output)

- Single-contract PDF with all cost/gross/net fields → 1 row, `parse_confidence = high`, `text_quality = digital`.
- PDF missing financial data (expected for old records) → 1 row, EUR fields NULL, `parse_confidence = medium`, no crash.
- Scanned PDF with clean OCR text → `text_quality = ocr_clean`.
- Scanned PDF with degraded OCR → `text_quality = ocr_degraded`, `parse_confidence = low`.
- PDF with zero extractable text → `text_quality = no_text`, 0 `position_rows`, `pdf_fetch_status = parse_error`.
- Multi-contract same-type PDF → N rows, same `contract_type`.
- Multi-contract mixed-type/mixed-subtype PDF → N rows, different `contract_type`/`contract_subtype`.
- PDF with different `section_structure_department` per row.
- Assegno di ricerca PDF with `Tipo A` / `Tipo B` entries.
- Old-format Assegno PDF (pre-2010, no Tipo A/B) → `contract_subtype = NULL`.

#### Failure handling tests

- PDF download returns 404 → `pdf_fetch_status = download_error`, sync continues, no crash.
- `mutool` not installed or exits non-zero → `pdf_fetch_status = parse_error`, sync continues.
- Detail page has no PDF link → `pdf_fetch_status = skipped`, no download attempted.
- `--force-refetch` flag causes cached PDF to be re-downloaded.

#### End-to-end smoke test

- `sync` runs without error; DB has rows across all 5 source types.
- Second `sync` run produces identical row counts (idempotency).
- `first_seen_at` is unchanged on second run; `last_synced_at` is updated.
- `position_rows_curated.csv` is non-empty; every row has `detail_id + position_row_index`.
- At least one `detail_id` has multiple `position_row_index` values.
- At least one call has `pdf_fetch_status = ok`.
- At least one call has `pdf_fetch_status = skipped` (old record without PDF).
- `text_quality` values present in output; `ocr_degraded` or `no_text` rows have `parse_confidence = low`.

---

### Assumptions and Defaults

- Source of truth for listing state: site membership only → `active` or `expired`.
- `ongoing/closed` is intentionally not produced in v1.
- `mutool` is required at runtime for PDF text extraction.
- Date parsing uses `DD-MM-YYYY`.
- All amounts are in EUR. Records start from 2003; pre-Euro Lire amounts are not expected.
- Any requested field may be missing: store `NULL` plus `NULL` evidence. Never crash on missing data.
- All HTML detail page fields are nullable. Missing HTML fields are stored as `NULL`, not an error.
- NULL EUR fields in old or undisclosing records are correct data. `parse_confidence` is behavioral only.
- `text_quality` reflects the PDF source quality independently of field extraction results.
- If one PDF contains multiple opportunities, each is a separate `position_rows` record.
- PDFs are cached indefinitely in `data/pdf_cache/`. Re-download only with `--force-refetch`.
- `first_seen_at` is set once and never overwritten. `last_synced_at` is updated on every sync.
- `numero_posti_html` reflects the HTML detail page value. PDF row count is implicit in `position_row_index`. Both are stored; neither overwrites the other.
- `section_structure_department` is row-level: different rows in the same PDF may have different values.
- `Assegno di ricerca` subtypes (`Tipo A` / `Tipo B`) apply only to records from 2010 onward. Earlier records have `contract_subtype = NULL` for this type.
- `detail_id` must remain stable across all future versions. Winner correlation in v2 will use it as a foreign key.
