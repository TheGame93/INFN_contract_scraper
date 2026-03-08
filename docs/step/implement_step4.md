# Step 4 — Fetch Layer

> **Location:** `docs/step/implement_step4.md`
> **Prerequisites:** Step 1 complete, Step 2 complete, Step 3 complete (including 3.3 TIPOS verified)
> **Produces:**
> - `src/infn_jobs/fetch/client.py`
> - `src/infn_jobs/fetch/listing/url_builder.py`
> - `src/infn_jobs/fetch/listing/parser.py`
> - `src/infn_jobs/fetch/detail/parser.py`
> - `src/infn_jobs/fetch/orchestrator.py`
> - `tests/fixtures/html/listing_active.html`
> - `tests/fixtures/html/listing_expired.html`
> - `tests/fixtures/html/detail_page_full.html`
> - `tests/fixtures/html/detail_page_old.html`
> - `tests/fetch/test_url_builder.py`
> - `tests/fetch/test_listing_parser.py`
> - `tests/fetch/test_detail_parser.py`

---

## 4.1 HTTP client

### 4.1.1 Create `src/infn_jobs/fetch/client.py`
- **File:** `src/infn_jobs/fetch/client.py`
- **Action:** Create
- **Write:**
  ```python
  def get_session() -> requests.Session:
      """Return a requests.Session with retry, backoff, and User-Agent configured."""
  ```
- **Test:** (manual verification — `python3 -c "from infn_jobs.fetch.client import get_session; s = get_session(); print(s.headers['User-Agent'])"` prints `infn-jobs-scraper/1.0 (research-tool)`)
- **Notes:**
  - Import `RATE_LIMIT_SLEEP`, `MAX_RETRIES`, `USER_AGENT` from `infn_jobs.config.settings`; never hardcode them here.
  - Mount a `HTTPAdapter` with `Retry(total=MAX_RETRIES, backoff_factor=1.0, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])` on both `http://` and `https://` prefixes.
  - Set `session.headers.update({"User-Agent": USER_AGENT})`.
  - Rate-limit sleep (1.0 s) is NOT enforced inside the session — it is the caller's responsibility (orchestrator sleeps between requests). `get_session()` only configures retry and identity.
  - No test file in `plan_implementation.md` for `client.py`; the session is exercised indirectly through listing/detail parser tests that use a mock session, and via e2e in Step 9.

[x] done

**Substep 4.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 4.2 Listing URL builder

### 4.2.1 Create `src/infn_jobs/fetch/listing/url_builder.py`
- **File:** `src/infn_jobs/fetch/listing/url_builder.py`
- **Action:** Create
- **Write:**
  ```python
  def build_urls(tipo: str) -> list[str]:
      """Return [active_url, expired_url] for the given tipo string."""
  ```
- **Test:** `pytest tests/fetch/test_url_builder.py -v` (test written in sub-substep 4.2.2)
- **Notes:**
  - Import `BASE_URL` from `infn_jobs.config.settings`.
  - Active URL: `f"{BASE_URL}/index.php?tipo={tipo}"`.
  - Expired URL: `f"{BASE_URL}/index.php?tipo={tipo}&scad=1"`.
  - Always returns exactly 2 URLs: index 0 = active, index 1 = expired. The orchestrator relies on this ordering to set `listing_status`.
  - `tipo` is one of the 5 strings from `TIPOS` — verified correct in Step 3.3.

[x] done

### 4.2.2 Create `tests/fetch/test_url_builder.py`
- **File:** `tests/fetch/test_url_builder.py`
- **Action:** Create
- **Write:**
  `test_build_urls_returns_two_urls`,
  `test_build_urls_active_url_has_no_scad`,
  `test_build_urls_expired_url_has_scad`,
  `test_build_urls_tipo_is_url_encoded_correctly`
- **Test:** `pytest tests/fetch/test_url_builder.py -v`
- **Notes:**
  - No fixture files needed — test data is inline.
  - `test_build_urls_returns_two_urls`: call `build_urls("Borsa")` and assert `len(result) == 2`.
  - `test_build_urls_active_url_has_no_scad`: assert `"scad"` not in `result[0]` and `"tipo=Borsa"` is in `result[0]`.
  - `test_build_urls_expired_url_has_scad`: assert `"scad=1"` in `result[1]` and `"tipo=Borsa"` in `result[1]`.
  - `test_build_urls_tipo_is_url_encoded_correctly`: call `build_urls("Incarico di ricerca")` and assert the URL contains the tipo string (check `"tipo=Incarico"` is present). Note: `requests` handles encoding at call time, but the URL string itself may or may not be percent-encoded depending on implementation choice — parametrize if both variants are valid.

[x] done

**Substep 4.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/fetch/test_url_builder.py -v` passes with no failures.

---

## 4.3 Listing HTML parser

### 4.3.1 Add fixture `tests/fixtures/html/listing_active.html`
- **File:** `tests/fixtures/html/listing_active.html`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 4.3.3 implementation and 4.4.1 test)
- **Notes:**
  - Minimal HTML page that reproduces the structure of the real `index.php?tipo=Borsa` page.
  - Must contain a `<table>` with at least 2 data rows. Each row represents one active call.
  - Each row must have a cell with a link: `<a href="dettagli_job.php?id=1234">dettaglio</a>` (relative href, no hostname). Use `id=1234` for row 1 and `id=1235` for row 2.
  - Rows should also have cells for: a BANDO identifier (e.g. `"123/2023"`), a title text (e.g. `"Borsa di studio"`), and a SCADENZA date string (e.g. `"31-01-2023"`). The exact column ordering should match what the real site returns — if unsure, write a generic version and update after Step 3.3 live verification.
  - Include a `<meta charset="utf-8">` tag so BeautifulSoup encoding detection works correctly on this fixture.

[x] done

### 4.3.2 Add fixture `tests/fixtures/html/listing_expired.html`
- **File:** `tests/fixtures/html/listing_expired.html`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 4.3.3 implementation and 4.4.1 test)
- **Notes:**
  - Same structure as `listing_active.html` but represents the `&scad=1` (expired) response.
  - Use different `id` values: `id=5000` and `id=5001` so tests can assert distinct `detail_id` values are returned for active vs. expired fixtures.
  - Include the same `<meta charset="utf-8">` tag.

[x] done

### 4.3.3 Create `src/infn_jobs/fetch/listing/parser.py`
- **File:** `src/infn_jobs/fetch/listing/parser.py`
- **Action:** Create
- **Write:**
  ```python
  def parse_rows(html: bytes) -> list[dict]:
      """Parse a listing page and return one dict per call row."""
  ```
- **Test:** `pytest tests/fetch/test_listing_parser.py -v` (test written in sub-substep 4.4.1)
- **Notes:**
  - `html` is `bytes` — pass directly to `BeautifulSoup(html, "lxml")`. Per CLAUDE.md: always pass `response.content` (bytes), never `response.text`. Let BeautifulSoup detect encoding from the `<meta charset>` tag.
  - Each returned dict must contain at minimum: `{"detail_id": str, "detail_url": str}`. Additional listing-visible fields (call number, deadline text) may also be included if reliably present across old and new pages — but omit rather than crash if a column is absent.
  - Extract `detail_id` from the `dettagli_job.php?id=<N>` href using `urllib.parse.parse_qs`. Private helper `_extract_detail_id(href: str) -> str | None` is acceptable.
  - Build `detail_url` as: if the href starts with `http`, use as-is; otherwise join with `BASE_URL` origin only (scheme + host: `https://jobs.dsi.infn.it`), per CLAUDE.md PDF URL resolution rule (same logic applies to detail page links).
  - If a row has no recognizable `dettagli_job.php?id=` link, skip the row (log at WARNING) — do not crash.
  - If the table is empty or absent, return `[]` — not an error.

[x] done

**Substep 4.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/fetch/ -v` passes with no failures.

---

## 4.4 Listing fixtures + tests

### 4.4.1 Create `tests/fetch/test_listing_parser.py`
- **File:** `tests/fetch/test_listing_parser.py`
- **Action:** Create
- **Write:**
  `test_parse_rows_active_returns_two_rows`,
  `test_parse_rows_active_detail_ids`,
  `test_parse_rows_expired_detail_ids`,
  `test_parse_rows_detail_url_is_absolute`,
  `test_parse_rows_empty_table_returns_empty_list`
- **Test:** `pytest tests/fetch/test_listing_parser.py -v`
- **Notes:**
  - Uses `tests/fixtures/html/listing_active.html` and `tests/fixtures/html/listing_expired.html`.
  - Load fixture bytes with `Path("tests/fixtures/html/listing_active.html").read_bytes()` or via a helper in `conftest.py`.
  - `test_parse_rows_active_returns_two_rows`: assert `len(result) == 2` for `listing_active.html`.
  - `test_parse_rows_active_detail_ids`: assert `result[0]["detail_id"] == "1234"` and `result[1]["detail_id"] == "1235"`.
  - `test_parse_rows_expired_detail_ids`: assert `result[0]["detail_id"] == "5000"` for `listing_expired.html`.
  - `test_parse_rows_detail_url_is_absolute`: assert `result[0]["detail_url"].startswith("http")` for both fixtures.
  - `test_parse_rows_empty_table_returns_empty_list`: pass a minimal HTML with no table rows and assert `parse_rows(html) == []`.

[x] done

**Substep 4.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/fetch/test_url_builder.py tests/fetch/test_listing_parser.py -v` passes with no failures.

---

## 4.5 Detail page parser

### 4.5.1 Add fixture `tests/fixtures/html/detail_page_full.html`
- **File:** `tests/fixtures/html/detail_page_full.html`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 4.5.3 implementation and 4.6.1 test)
- **Notes:**
  - Reproduces the structure of the real `dettagli_job.php?id=1234` page with all fields present.
  - Must include a labeled table (or `<dl>`, or whatever structure the real page uses) with all of the following fields visible:
    - `Numero`: `"123/2023"`
    - `Anno`: `"2023"`
    - `Titolo`: `"Borsa di studio per attività di ricerca"`
    - `Numero posti`: `"1"`
    - `Tipo`: `"Borsa"`
    - `Data bando`: `"01-01-2023"`
    - `Data scadenza`: `"31-01-2023"`
    - `Bando (PDF)`: `<a href="/bandi/bando123.pdf">download</a>` (relative href)
  - Include `<meta charset="utf-8">`.
  - Use `detail_id=1234` as the assumed page ID (the parser receives this as a parameter).

[x] done

### 4.5.2 Add fixture `tests/fixtures/html/detail_page_old.html`
- **File:** `tests/fixtures/html/detail_page_old.html`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 4.5.3 implementation and 4.6.1 test)
- **Notes:**
  - Represents an older record with missing fields — must NOT have a `Numero posti` row and must NOT have a `Bando (PDF)` link.
  - Still has: `Numero`, `Anno`, `Titolo`, `Tipo`, `Data scadenza`. May omit `Data bando` as well (common in old records).
  - Include `<meta charset="iso-8859-1">` to exercise the encoding-detection path — BeautifulSoup must handle this correctly because bytes are passed in.
  - Use `detail_id=9999` as the assumed page ID.

[x] done

### 4.5.3 Create `src/infn_jobs/fetch/detail/parser.py`
- **File:** `src/infn_jobs/fetch/detail/parser.py`
- **Action:** Create
- **Write:**
  ```python
  def parse_detail(html: bytes, detail_id: str) -> CallRaw:
      """Parse a detail page and return a CallRaw with all available fields."""
  ```
- **Test:** `pytest tests/fetch/test_detail_parser.py -v` (test written in sub-substep 4.6.1)
- **Notes:**
  - `html` is `bytes` — pass directly to `BeautifulSoup(html, "lxml")`. Never use `response.text`.
  - Import `CallRaw` from `infn_jobs.domain.call`; import `BASE_URL` from `infn_jobs.config.settings`.
  - Set `call.detail_id = detail_id` unconditionally (always known from the URL).
  - Set `call.detail_url = f"{BASE_URL}/dettagli_job.php?id={detail_id}"`.
  - **All other fields are nullable.** If a field's label is not found on the page, store `None` — never raise.
  - `numero_posti_html`: parse the integer value; if the field is absent or non-numeric, store `None`.
  - `pdf_url`: if `Bando (PDF)` link exists, resolve the href — if it starts with `http`, use as-is; otherwise join with `BASE_URL` origin (scheme + host only, e.g. `https://jobs.dsi.infn.it`). Per CLAUDE.md. If no link, store `None`.
  - Do NOT set `listing_status`, `source_tipo`, `pdf_call_title`, `pdf_fetch_status`, `pdf_cache_path`, `first_seen_at`, `last_synced_at` — those are set by the orchestrator or store layer.
  - Log field parsing at DEBUG level. Log a WARNING if an unexpected page structure is encountered (e.g., no table found at all), but still return the partially-filled `CallRaw`.

[x] done

**Substep 4.5 done when:** all sub-substeps above are `[x]` and
`pytest tests/fetch/ -v` passes with no failures.

---

## 4.6 Detail page fixtures + tests

### 4.6.1 Create `tests/fetch/test_detail_parser.py`
- **File:** `tests/fetch/test_detail_parser.py`
- **Action:** Create
- **Write:**
  `test_parse_detail_full_page_all_fields`,
  `test_parse_detail_full_page_pdf_url_resolved`,
  `test_parse_detail_old_page_numero_posti_is_none`,
  `test_parse_detail_old_page_pdf_url_is_none`,
  `test_parse_detail_sets_detail_id`,
  `test_parse_detail_pdf_url_absolute_used_as_is`,
  `test_parse_detail_returns_call_raw_instance`
- **Test:** `pytest tests/fetch/test_detail_parser.py -v`
- **Notes:**
  - Uses `tests/fixtures/html/detail_page_full.html` and `tests/fixtures/html/detail_page_old.html`.
  - `test_parse_detail_full_page_all_fields`: parse `detail_page_full.html` with `detail_id="1234"`; assert `result.numero == "123/2023"`, `result.anno == "2023"`, `result.titolo` is not None, `result.numero_posti_html == 1`, `result.data_scadenza == "31-01-2023"`.
  - `test_parse_detail_full_page_pdf_url_resolved`: assert `result.pdf_url.startswith("http")` — relative `/bandi/bando123.pdf` is joined with `BASE_URL` origin.
  - `test_parse_detail_old_page_numero_posti_is_none`: parse `detail_page_old.html` with `detail_id="9999"`; assert `result.numero_posti_html is None`.
  - `test_parse_detail_old_page_pdf_url_is_none`: assert `result.pdf_url is None`.
  - `test_parse_detail_sets_detail_id`: assert `result.detail_id == "1234"` for the full-page fixture.
  - `test_parse_detail_pdf_url_absolute_used_as_is`: construct a minimal HTML with `href="https://external.example.com/bando.pdf"` and assert `result.pdf_url == "https://external.example.com/bando.pdf"`.
  - `test_parse_detail_returns_call_raw_instance`: assert `isinstance(result, CallRaw)`.
  - For the inline absolute-URL test, pass minimal HTML bytes directly (no fixture file needed for that case).

[x] done

**Substep 4.6 done when:** all sub-substeps above are `[x]` and
`pytest tests/fetch/test_detail_parser.py -v` passes with no failures.

---

## 4.7 Fetch orchestrator

### 4.7.1 Create `src/infn_jobs/fetch/orchestrator.py`
- **File:** `src/infn_jobs/fetch/orchestrator.py`
- **Action:** Create
- **Write:**
  ```python
  def fetch_all_calls(session: requests.Session, tipo: str) -> list[CallRaw]:
      """Fetch all active and expired calls for one tipo. Returns assembled CallRaw list."""
  ```
- **Test:** (manual verification — covered by e2e in Step 9; no unit test file in `plan_implementation.md` for the orchestrator)
- **Notes:**
  - Import `build_urls` from `infn_jobs.fetch.listing.url_builder`; `parse_rows` from `infn_jobs.fetch.listing.parser`; `parse_detail` from `infn_jobs.fetch.detail.parser`; `RATE_LIMIT_SLEEP` from `infn_jobs.config.settings`; `CallRaw` from `infn_jobs.domain.call`.
  - Per CLAUDE.md: `fetch_all_calls` calls `parse_rows()` to get listing dicts, then for each row calls `parse_detail()` to build `CallRaw`. Sets `listing_status` from the URL variant used (`"active"` for index 0, `"expired"` for index 1 from `build_urls()`). Returns the assembled `CallRaw` list.
  - Sleep `RATE_LIMIT_SLEEP` seconds (via `time.sleep`) **between every HTTP GET** — after each listing page fetch and after each detail page fetch. Do not sleep before the very first request.
  - Set `call.source_tipo = tipo` on every assembled `CallRaw`.
  - Pass `response.content` (bytes) to `parse_rows()` and `parse_detail()` — never `response.text`.
  - On HTTP error fetching a detail page: log at WARNING and **skip** that call entirely — do not create a `CallRaw` for it. The `detail_id` from the listing row is known, but since `parse_detail()` was never called, no `CallRaw` is available to populate. The next sync run will retry. Do not set `pdf_fetch_status` here — that field reflects PDF-level outcomes, not HTML detail page fetch outcomes.
  - Log at INFO: `"Fetching tipo {tipo} (active)"` and `"Fetching tipo {tipo} (expired)"` before each listing URL; `"Processing detail_id={detail_id}"` before each detail fetch.
  - Use `logging.getLogger(__name__)` — no `print()` per CLAUDE.md logging standard.

[x] done

**Substep 4.7 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 4.8 Zero-row verification

### 4.8.1 Verify all 5 tipos return non-empty listings
- **File:** (no file — manual verification)
- **Action:** (verification)
- **Write:** (no code)
- **Test:** (manual verification — for each of the 5 verified TIPOS, open `{BASE_URL}/index.php?tipo={tipo}` and confirm the page contains at least one listing row. Also check `{BASE_URL}/index.php?tipo={tipo}&scad=1` for expired listings. If any tipo returns 0 rows, investigate for pagination params and document in `docs/known_edge_cases.md`.)
- **Notes:**
  - Per CLAUDE.md: "If any tipo returns 0 rows, investigate for pagination params, update `url_builder.py`, and document in `docs/known_edge_cases.md`."
  - This check should also be performed by the orchestrator at runtime: if `parse_rows()` returns `[]` for a listing URL, log at WARNING.

[x] done

**Substep 4.8 done when:** all sub-substeps above are `[x]`.

---

## Verification

```bash
pytest tests/fetch/ -v
ruff check src/infn_jobs/fetch/
```

Expected: all fetch layer tests green, ruff exits 0.

Manual checks:
- `python3 -c "from infn_jobs.fetch.client import get_session; s = get_session(); print(s.headers['User-Agent'])"` prints `infn-jobs-scraper/1.0 (research-tool)`.
- `python3 -c "from infn_jobs.fetch.listing.url_builder import build_urls; print(build_urls('Borsa'))"` prints two URLs, first without `scad`, second with `scad=1`.
- `python3 -c "from infn_jobs.fetch.orchestrator import fetch_all_calls"` imports without error.
