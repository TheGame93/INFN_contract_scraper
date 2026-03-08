# Step 5 — Extract Layer

> **Location:** `docs/step/implement_step5.md`
> **Prerequisites:** Step 1 complete, Step 2 complete, Step 3 complete
> **Produces:**
> - `src/infn_jobs/extract/pdf/downloader.py`
> - `src/infn_jobs/extract/pdf/mutool.py`
> - `src/infn_jobs/extract/parse/normalize/currency.py`
> - `src/infn_jobs/extract/parse/normalize/dates.py`
> - `src/infn_jobs/extract/parse/normalize/subtypes.py`
> - `src/infn_jobs/extract/parse/segmenter.py`
> - `src/infn_jobs/extract/parse/fields/metadata.py`
> - `src/infn_jobs/extract/parse/fields/contract_type.py`
> - `src/infn_jobs/extract/parse/fields/duration.py`
> - `src/infn_jobs/extract/parse/fields/income.py`
> - `src/infn_jobs/extract/parse/fields/confidence.py`
> - `src/infn_jobs/extract/parse/row_builder.py`
> - `tests/fixtures/pdf_text/single_contract.txt`
> - `tests/fixtures/pdf_text/missing_fields.txt`
> - `tests/fixtures/pdf_text/multi_same_type.txt`
> - `tests/fixtures/pdf_text/multi_mixed_type.txt`
> - `tests/fixtures/pdf_text/multi_mixed_department.txt`
> - `tests/fixtures/pdf_text/ocr_clean.txt`
> - `tests/fixtures/pdf_text/ocr_degraded.txt`
> - `tests/fixtures/pdf_text/assegno_tipo_ab.txt`
> - `tests/fixtures/pdf_text/assegno_old.txt`
> - `tests/extract/test_mutool.py`
> - `tests/extract/test_segmenter.py`
> - `tests/extract/fields/test_contract_type.py`
> - `tests/extract/fields/test_duration.py`
> - `tests/extract/fields/test_income.py`
> - `tests/extract/normalize/test_currency.py`
> - `tests/extract/normalize/test_dates.py`
> - `tests/extract/normalize/test_subtypes.py`
> - `tests/extract/fields/test_confidence.py`
> - `tests/extract/test_row_builder.py`

Note on fixture-first ordering: substep 5.8 creates all 9 PDF text fixtures before any field
extractor or segmenter is written (5.9–5.16). The fixture-first rule is satisfied at the
substep level — complete 5.8 before starting 5.9.

---

## 5.1 PDF downloader

### 5.1.1 Create `src/infn_jobs/extract/pdf/downloader.py`
- **File:** `src/infn_jobs/extract/pdf/downloader.py`
- **Action:** Create
- **Write:**
  ```python
  def download(
      url: str | None,
      dest: Path,
      session: requests.Session | None = None,
      force: bool = False,
  ) -> Path | None:
      """Download PDF to dest. Returns dest on success, None if url is None."""
  ```
- **Test:** (manual verification — no dedicated test file in `plan_implementation.md`; downloader is exercised via e2e in Step 9; verify manually: `python3 -c "from infn_jobs.extract.pdf.downloader import download; print('ok')"`)
- **Notes:**
  - If `url` is `None` or empty string, return `None` immediately — do not attempt download.
  - If `dest` already exists and `force=False`, return `dest` immediately (cache hit). Log at DEBUG: `"PDF {dest.name}: cache hit, skipping download"`.
  - **Session parameter:** if `session` is provided, use it for the HTTP GET (inherits retry/backoff config from `get_session()`). If `None`, create a short-lived `requests.Session` with `USER_AGENT` header set. The pipeline (Step 7) passes the same session used for fetch operations.
  - **Rate limiting:** call `time.sleep(RATE_LIMIT_SLEEP)` before the HTTP GET (not before cache hits). Import `RATE_LIMIT_SLEEP` from `infn_jobs.config.settings`. Per CLAUDE.md: "1.0 s sleep between requests" applies to PDF downloads too.
  - On HTTP error (non-200 response): do NOT retry 4xx (per CLAUDE.md). Log at WARNING and return `None`. The caller (pipeline Step 7) sets `pdf_fetch_status = "download_error"`.
  - On success: write `response.content` (bytes) to `dest` and return `dest`. Create parent dirs with `dest.parent.mkdir(parents=True, exist_ok=True)`.
  - Per CLAUDE.md: "PDF URL resolution — if the href starts with `http`, use as-is. Otherwise join with BASE_URL origin (scheme + host only, not path)." URL resolution is done in the detail parser (Step 4); by the time `download()` is called, `url` is already absolute.
  - Log at INFO: `"PDF {dest.name}: downloaded"` on success.

[ ] done

**Substep 5.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.2 `mutool` wrapper

### 5.2.1 Create `src/infn_jobs/extract/pdf/mutool.py`
- **File:** `src/infn_jobs/extract/pdf/mutool.py`
- **Action:** Create
- **Write:**
  ```python
  def extract_text(pdf_path: Path) -> tuple[str, TextQuality]:
      """Run mutool draw -F txt on pdf_path. Returns (text, text_quality)."""
  ```
- **Test:** `pytest tests/extract/test_mutool.py -v` (test written in sub-substep 5.3.1)
- **Notes:**
  - Run: `subprocess.run(["mutool", "draw", "-F", "txt", str(pdf_path)], capture_output=True, text=True, timeout=60)`.
  - On non-zero return code or `FileNotFoundError` (mutool not installed): raise `RuntimeError`. The pipeline (Step 7) catches this and sets `pdf_fetch_status = "parse_error"`.
  - `text_quality` classification (applied to `result.stdout`):
    - `TextQuality.NO_TEXT`: output is empty or fewer than 50 characters after stripping whitespace.
    - `TextQuality.OCR_DEGRADED`: ratio of non-alphanumeric/non-space characters exceeds 0.30 of total (after removing whitespace). Signals garbled OCR.
    - `TextQuality.OCR_CLEAN`: readable text but includes OCR-typical artifacts — heuristic: presence of form-feed `\x0c` page separators and at least one recognizable Italian word (e.g., `durata`, `sezione`, `compenso`, `bando`). If text is clean but below OCR signal threshold, classify as `digital`.
    - `TextQuality.DIGITAL`: all other readable output.
  - Import `TextQuality` from `infn_jobs.domain.enums`.
  - Pages in mutool output are separated by form-feed `\x0c` — preserve these in the returned text; `segment()` in Step 5.9 uses them as split hints.
  - Log at DEBUG: `"mutool {pdf_path.name}: {text_quality.value}, {len(text)} chars"`.

[ ] done

**Substep 5.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.3 `mutool` tests

### 5.3.1 Create `tests/extract/test_mutool.py`
- **File:** `tests/extract/test_mutool.py`
- **Action:** Create
- **Write:**
  `test_extract_text_ok_returns_text_and_digital`,
  `test_extract_text_empty_output_returns_no_text`,
  `test_extract_text_garbled_returns_ocr_degraded`,
  `test_extract_text_subprocess_failure_raises`,
  `test_extract_text_mutool_not_found_raises`
- **Test:** `pytest tests/extract/test_mutool.py -v`
- **Notes:**
  - No real PDFs or fixture files — mock `subprocess.run` using `unittest.mock.patch`.
  - `test_extract_text_ok_returns_text_and_digital`: mock returns `CompletedProcess(returncode=0, stdout="CONTRATTO DI RICERCA\nDurata: 12 mesi\nCompenso lordo annuo: € 28.000,00\n")` — assert `text_quality == TextQuality.DIGITAL` and text is non-empty.
  - `test_extract_text_empty_output_returns_no_text`: mock returns `returncode=0, stdout="   \n"` — assert `text_quality == TextQuality.NO_TEXT`.
  - `test_extract_text_garbled_returns_ocr_degraded`: mock returns `returncode=0, stdout="C0NTR4TT0 Dl R|C3RC4 @#$%^& !!!! |||"` — assert `text_quality == TextQuality.OCR_DEGRADED`.
  - `test_extract_text_subprocess_failure_raises`: mock returns `returncode=1, stdout=""` — assert `extract_text(path)` raises `RuntimeError`.
  - `test_extract_text_mutool_not_found_raises`: mock `subprocess.run` raises `FileNotFoundError` — assert `extract_text(path)` raises `RuntimeError`.
  - Pass a `tmp_path / "dummy.pdf"` as the path argument (does not need to exist for mocked calls).

[ ] done

**Substep 5.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/test_mutool.py -v` passes with no failures.

---

## 5.4 EUR normalization

### 5.4.1 Create `src/infn_jobs/extract/parse/normalize/currency.py`
- **File:** `src/infn_jobs/extract/parse/normalize/currency.py`
- **Action:** Create
- **Write:**
  ```python
  def normalize_eur(s: str | None) -> float | None:
      """Normalize Italian-format EUR string to float. Returns None if unparseable."""
  ```
- **Test:** `pytest tests/extract/normalize/test_currency.py -v` (test written in sub-substep 5.7.1)
- **Notes:**
  - Input variants to handle: `"33.681,30"` → `33681.30`; `"1200"` → `1200.0`; `"€ 1.200,00"` → `1200.0`; `"1.200"` (no cents) → `1200.0`; line-broken number `"33.681\n,30"` → normalize whitespace first.
  - Algorithm: strip `€`, `EUR`, whitespace, and non-numeric characters except `.` and `,`; collapse whitespace and line breaks; if a `,` is present, treat it as decimal separator and `.` as thousands separator; otherwise treat `.` as decimal.
  - Return `None` for `None` input, empty string, or any string that cannot be parsed after cleaning.
  - Pure function — no I/O, no imports from other `infn_jobs` modules.

[ ] done

**Substep 5.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.5 Date normalization

### 5.5.1 Create `src/infn_jobs/extract/parse/normalize/dates.py`
- **File:** `src/infn_jobs/extract/parse/normalize/dates.py`
- **Action:** Create
- **Write:**
  ```python
  def parse_date(s: str | None) -> date | None:
      """Parse a date string in DD-MM-YYYY or DD/MM/YYYY format. Returns None if invalid."""
  ```
- **Test:** `pytest tests/extract/normalize/test_dates.py -v` (test written in sub-substep 5.7.2)
- **Notes:**
  - Primary format: `DD-MM-YYYY` (per CLAUDE.md). Also accept `DD/MM/YYYY` as an alternate separator.
  - Return `None` for `None` input, empty string, or any string that cannot be parsed.
  - Return `datetime.date` object on success.
  - Do not attempt fuzzy parsing — only the two explicit formats.
  - Pure function — no I/O, no imports from other `infn_jobs` modules (only `datetime`).

[ ] done

**Substep 5.5 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.6 Subtype normalization

### 5.6.1 Create `src/infn_jobs/extract/parse/normalize/subtypes.py`
- **File:** `src/infn_jobs/extract/parse/normalize/subtypes.py`
- **Action:** Create
- **Write:**
  ```python
  def normalize_subtype(s: str | None, anno: int | None) -> str | None:
      """Normalize contract subtype string to canonical form. Era-aware for Assegno subtypes."""
  ```
- **Test:** `pytest tests/extract/normalize/test_subtypes.py -v` (test written in sub-substep 5.7.3)
- **Notes:**
  - Per CLAUDE.md key conventions:
    - `"Fascia II"` → canonical `"Fascia 2"` (case-insensitive match on `fascia ii`).
    - `"Tipo A"` → canonical `"Tipo A"` (post-2010 only; if `anno < 2010` or `anno is None`, return `None`).
    - `"Tipo B"` → canonical `"Tipo B"` (same era rule).
  - Per CLAUDE.md: "Pre-2010 (L. 449/1997): single type, no `Tipo A / B` distinction. Post-2010 (L. 240/2010 Gelmini reform, art. 22): `Tipo A` and `Tipo B`."
  - For `Tipo A/B` inputs: if `anno is None`, return `None` (cannot determine era — conservative approach).
  - For unrecognized input with `anno >= 2010`, return the input normalized (strip/title-case) rather than `None` — allows unknown subtypes to pass through.
  - Return `None` for `None` input or empty string.
  - Pure function — no I/O, no imports from other `infn_jobs` modules (only stdlib).

[ ] done

**Substep 5.6 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.7 Normalization tests

### 5.7.1 Create `tests/extract/normalize/test_currency.py`
- **File:** `tests/extract/normalize/test_currency.py`
- **Action:** Create
- **Write:**
  `test_normalize_eur_italian_format`,
  `test_normalize_eur_plain_integer`,
  `test_normalize_eur_plain_decimal`,
  `test_normalize_eur_with_euro_symbol`,
  `test_normalize_eur_line_broken_number`,
  `test_normalize_eur_thousands_only_no_cents`,
  `test_normalize_eur_none_returns_none`,
  `test_normalize_eur_empty_returns_none`,
  `test_normalize_eur_unparseable_returns_none`
- **Test:** `pytest tests/extract/normalize/test_currency.py -v`
- **Notes:**
  - All test data is inline — no fixture files.
  - `test_normalize_eur_italian_format`: `normalize_eur("33.681,30")` → `pytest.approx(33681.30)`.
  - `test_normalize_eur_plain_integer`: `normalize_eur("1200")` → `1200.0`.
  - `test_normalize_eur_plain_decimal`: `normalize_eur("1200.50")` → `1200.50` (decimal point, no thousands).
  - `test_normalize_eur_with_euro_symbol`: `normalize_eur("€ 1.200,00")` → `1200.0`.
  - `test_normalize_eur_line_broken_number`: `normalize_eur("33.681\n,30")` → `pytest.approx(33681.30)`.
  - `test_normalize_eur_thousands_only_no_cents`: `normalize_eur("1.200")` → `1200.0`.
  - Consider `@pytest.mark.parametrize` for the valid-input cases.

[ ] done

### 5.7.2 Create `tests/extract/normalize/test_dates.py`
- **File:** `tests/extract/normalize/test_dates.py`
- **Action:** Create
- **Write:**
  `test_parse_date_ddmmyyyy_hyphen`,
  `test_parse_date_ddmmyyyy_slash`,
  `test_parse_date_returns_date_object`,
  `test_parse_date_none_returns_none`,
  `test_parse_date_empty_returns_none`,
  `test_parse_date_invalid_date_returns_none`,
  `test_parse_date_wrong_format_returns_none`
- **Test:** `pytest tests/extract/normalize/test_dates.py -v`
- **Notes:**
  - All test data is inline — no fixture files.
  - `test_parse_date_ddmmyyyy_hyphen`: `parse_date("31-01-2023")` → `date(2023, 1, 31)`.
  - `test_parse_date_ddmmyyyy_slash`: `parse_date("31/01/2023")` → `date(2023, 1, 31)`.
  - `test_parse_date_wrong_format_returns_none`: `parse_date("2023-01-31")` (ISO format) → `None` — the function only handles DD-MM-YYYY and DD/MM/YYYY.
  - `test_parse_date_invalid_date_returns_none`: `parse_date("32-13-2023")` → `None`.

[ ] done

### 5.7.3 Create `tests/extract/normalize/test_subtypes.py`
- **File:** `tests/extract/normalize/test_subtypes.py`
- **Action:** Create
- **Write:**
  `test_normalize_subtype_fascia_ii_to_fascia_2`,
  `test_normalize_subtype_fascia_ii_case_insensitive`,
  `test_normalize_subtype_tipo_a_post2010`,
  `test_normalize_subtype_tipo_b_post2010`,
  `test_normalize_subtype_tipo_a_pre2010_returns_none`,
  `test_normalize_subtype_tipo_a_anno_none_returns_none`,
  `test_normalize_subtype_none_input_returns_none`,
  `test_normalize_subtype_empty_returns_none`
- **Test:** `pytest tests/extract/normalize/test_subtypes.py -v`
- **Notes:**
  - All test data is inline — no fixture files.
  - `test_normalize_subtype_fascia_ii_to_fascia_2`: `normalize_subtype("Fascia II", 2015)` → `"Fascia 2"`.
  - `test_normalize_subtype_fascia_ii_case_insensitive`: `normalize_subtype("fascia ii", 2005)` → `"Fascia 2"` (era does not gate Fascia normalization).
  - `test_normalize_subtype_tipo_a_post2010`: `normalize_subtype("Tipo A", 2015)` → `"Tipo A"`.
  - `test_normalize_subtype_tipo_b_post2010`: `normalize_subtype("Tipo B", 2012)` → `"Tipo B"`.
  - `test_normalize_subtype_tipo_a_pre2010_returns_none`: `normalize_subtype("Tipo A", 2008)` → `None`.
  - `test_normalize_subtype_tipo_a_anno_none_returns_none`: `normalize_subtype("Tipo A", None)` → `None`.

[ ] done

**Substep 5.7 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/normalize/ -v` passes with no failures.

---

## 5.8 PDF text fixtures

> All 9 fixtures are plain-text files representing `mutool draw -F txt` output for different
> PDF scenarios. They are used by the segmenter, field extractors, and row builder tests.
> **Complete all 9 before beginning substep 5.9.**

### 5.8.1 Add fixture `tests/fixtures/pdf_text/single_contract.txt`
- **File:** `tests/fixtures/pdf_text/single_contract.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substeps 5.9.2, 5.15.1–5.15.3)
- **Notes:**
  - Scenario: digital PDF, single contract entry, all fields present.
  - Must contain recognizable labels for all 7 EUR fields, duration, contract type, and section. Use realistic Italian text:
    ```
    CONTRATTO DI RICERCA
    Sezione di Roma 1
    Durata: 12 mesi
    Costo a carico dell'Ente: € 33.681,30
    Compenso lordo annuo: € 28.000,00
    Compenso lordo totale: € 28.000,00
    Compenso netto mensile: € 1.800,00
    Compenso netto annuo: € 21.600,00
    Compenso netto totale: € 21.600,00
    ```
  - No form-feed `\x0c` separators (single page).
  - Must NOT contain garbled characters — `text_quality` should be classified as `digital`.

[ ] done

### 5.8.2 Add fixture `tests/fixtures/pdf_text/missing_fields.txt`
- **File:** `tests/fixtures/pdf_text/missing_fields.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substeps 5.9.2, 5.15.1–5.15.3)
- **Notes:**
  - Scenario: old record — financial fields absent, duration present, contract type present.
  - Contains contract type and duration labels but NO EUR amount lines. This exercises the parse_confidence = medium path (contract_type parsed, no financial data found).
    ```
    BORSA DI STUDIO
    Sezione di Frascati
    Durata: 12 mesi
    ```
  - All 7 EUR fields should parse as `None` from this fixture — that is correct data, not a parse failure.

[ ] done

### 5.8.3 Add fixture `tests/fixtures/pdf_text/multi_same_type.txt`
- **File:** `tests/fixtures/pdf_text/multi_same_type.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substeps 5.9.2, 5.15.1–5.15.3)
- **Notes:**
  - Scenario: 2 contract entries in the same PDF, same contract_type (`Contratto di ricerca`).
  - The segmenter must split this into 2 segments. Use a repeated entry pattern with a clear separator:
    ```
    CONTRATTO DI RICERCA - n. 1
    Sezione di Torino
    Durata: 12 mesi
    Compenso lordo annuo: € 25.000,00

    CONTRATTO DI RICERCA - n. 2
    Sezione di Milano
    Durata: 24 mesi
    Compenso lordo annuo: € 26.000,00
    ```
  - After segmentation, both rows should have `contract_type` populated and the same canonical type.

[ ] done

### 5.8.4 Add fixture `tests/fixtures/pdf_text/multi_mixed_type.txt`
- **File:** `tests/fixtures/pdf_text/multi_mixed_type.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substeps 5.9.2, 5.15.1–5.15.3)
- **Notes:**
  - Scenario: 2+ entries with different contract types and/or subtypes (e.g., one `Borsa di studio` and one `Incarico di ricerca`).
  - Must produce multiple `PositionRow` objects with different `contract_type` values after row building.
    ```
    BORSA DI STUDIO - n. 1
    Sezione di Genova
    Durata: 12 mesi

    INCARICO DI RICERCA - n. 1
    Sezione di Catania
    Durata: 18 mesi
    ```

[ ] done

### 5.8.5 Add fixture `tests/fixtures/pdf_text/multi_mixed_department.txt`
- **File:** `tests/fixtures/pdf_text/multi_mixed_department.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substeps 5.9.2, 5.15.1–5.15.3)
- **Notes:**
  - Scenario: multiple entries sharing contract_type but with DIFFERENT `section_structure_department` per row. Exercises row-level section extraction.
    ```
    CONTRATTO DI RICERCA - n. 1
    Sezione di Bologna
    Durata: 12 mesi

    CONTRATTO DI RICERCA - n. 2
    Sezione di Napoli
    Durata: 12 mesi
    ```
  - After row building, `position_row_index=0` has `section_structure_department="Sezione di Bologna"` and `position_row_index=1` has `section_structure_department="Sezione di Napoli"`.

[ ] done

### 5.8.6 Add fixture `tests/fixtures/pdf_text/ocr_clean.txt`
- **File:** `tests/fixtures/pdf_text/ocr_clean.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 5.3.1 and 5.9.2)
- **Notes:**
  - Scenario: scanned PDF with clean OCR — text is readable but has typical OCR artifacts (extra spaces, occasional mis-recognized characters).
  - Must include at least one `\x0c` form-feed separator (simulates multi-page scanned output).
  - Field labels recognizable but slightly imperfect:
    ```
    BORSA  DI  STUDIO\x0c
    Sezi one di Pisa
    Dura ta: 12 me si
    ```
  - `text_quality` classification should produce `OCR_CLEAN` (readable but with OCR signals).

[ ] done

### 5.8.7 Add fixture `tests/fixtures/pdf_text/ocr_degraded.txt`
- **File:** `tests/fixtures/pdf_text/ocr_degraded.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 5.3.1 and 5.9.2)
- **Notes:**
  - Scenario: heavily garbled OCR output — non-alphanumeric character ratio exceeds 0.30.
  - Must trigger `TextQuality.OCR_DEGRADED` classification in `mutool.py`. Example content that achieves >30% non-word chars:
    ```
    C0NTR4TT0 Dl R|C3RCA @#$%^& !!!! ||| Bnd0 p@r !!
    D!!r4t4: 12 m@$!! ##
    C0mp3ns0 l0rd0: @#$ |||
    ```
  - `parse_confidence` should be `low` for rows derived from this text.

[ ] done

### 5.8.8 Add fixture `tests/fixtures/pdf_text/assegno_tipo_ab.txt`
- **File:** `tests/fixtures/pdf_text/assegno_tipo_ab.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 5.15.1)
- **Notes:**
  - Scenario: Assegno di ricerca PDF (post-2010), with distinct Tipo A and Tipo B entries.
  - Must contain both subtypes so `contract_subtype` canonical form is extracted correctly per entry:
    ```
    ASSEGNO DI RICERCA - Tipo A
    Art. 22 L. 240/2010
    Sezione di Padova
    Durata: 36 mesi

    ASSEGNO DI RICERCA - Tipo B
    Art. 22 L. 240/2010
    Sezione di Roma
    Durata: 36 mesi
    ```
  - After row building with `anno=2015`, row 0: `contract_subtype="Tipo A"`, row 1: `contract_subtype="Tipo B"`.

[ ] done

### 5.8.9 Add fixture `tests/fixtures/pdf_text/assegno_old.txt`
- **File:** `tests/fixtures/pdf_text/assegno_old.txt`
- **Action:** Create
- **Write:** (fixture file — no function; content described in Notes)
- **Test:** (tested by sub-substep 5.15.1)
- **Notes:**
  - Scenario: Assegno di ricerca PDF (pre-2010, L. 449/1997) — NO Tipo A/B mention. Single type.
  - After row building with `anno=2007`, `contract_subtype` must be `None` (era gate applied).
    ```
    ASSEGNO DI RICERCA
    Legge 449/1997
    Sezione di Frascati
    Durata: 12 mesi (rinnovabile per un secondo anno)
    ```
  - `contract_subtype_raw` is also `None` since the subtype is not mentioned at all.

[ ] done

**Substep 5.8 done when:** all sub-substeps above are `[x]` and all 9 fixture files exist under
`tests/fixtures/pdf_text/`.

---

## 5.9 Segmenter

### 5.9.1 Create `src/infn_jobs/extract/parse/segmenter.py`
- **File:** `src/infn_jobs/extract/parse/segmenter.py`
- **Action:** Create
- **Write:**
  ```python
  def segment(text: str) -> list[str]:
      """Split mutool text output into per-entry segments. Returns list with at least one element."""
  ```
- **Test:** `pytest tests/extract/test_segmenter.py -v` (test written in sub-substep 5.9.2)
- **Notes:**
  - Per plan_desiderata: "Split by repeated patterns (`n.`, `contratto`, `incarico`, `fascia`, `assegno`, article blocks/tables)."
  - A second entry is signalled by a line that starts a new contract header — e.g., `CONTRATTO DI RICERCA - n. 2`, a new `BORSA`, `INCARICO`, `ASSEGNO` keyword at the start of a line, or a line matching `n\. \d+` followed by a type keyword.
  - Also split on form-feed `\x0c` page boundaries if a new contract header immediately follows.
  - If no split point is found, return `[text]` — a list with one element (the full text).
  - Never return `[]` — always at least one segment.
  - Strip leading/trailing whitespace from each segment.
  - Position is determined by order of appearance — `position_row_index` = 0-based index in the returned list. Per CLAUDE.md: "Deterministic for identical PDF text. Never reorder."
  - Pure text processing — no I/O, no imports from other `infn_jobs` modules.

[ ] done

### 5.9.2 Create `tests/extract/test_segmenter.py`
- **File:** `tests/extract/test_segmenter.py`
- **Action:** Create
- **Write:**
  `test_segment_single_entry_returns_one_segment`,
  `test_segment_multi_same_type_returns_two_segments`,
  `test_segment_multi_mixed_type_returns_multiple`,
  `test_segment_empty_text_returns_single_empty`,
  `test_segment_preserves_content_of_first_segment`,
  `test_segment_page_break_splits_on_new_header`
- **Test:** `pytest tests/extract/test_segmenter.py -v`
- **Notes:**
  - Uses fixtures: `single_contract.txt` (→ 1 segment), `multi_same_type.txt` (→ 2 segments), `multi_mixed_type.txt` (→ ≥2 segments), `ocr_clean.txt` (→ 1 or more, test that it doesn't crash), `ocr_degraded.txt` (→ 1 segment expected, garbled).
  - Load fixtures via `Path("tests/fixtures/pdf_text/<name>.txt").read_text()` or a helper.
  - `test_segment_empty_text_returns_single_empty`: `segment("")` → `[""]` (list of one empty string, not `[]`).
  - `test_segment_preserves_content_of_first_segment`: the first segment of `single_contract.txt` must contain the string `"CONTRATTO DI RICERCA"`.

[ ] done

**Substep 5.9 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/test_segmenter.py -v` passes with no failures.

---

## 5.10 Field extractor: `metadata.py`

### 5.10.1 Create `src/infn_jobs/extract/parse/fields/metadata.py`
- **File:** `src/infn_jobs/extract/parse/fields/metadata.py`
- **Action:** Create
- **Write:**
  ```python
  def extract_pdf_call_title(text: str) -> str | None:
      """Extract call-level title from full PDF text (before segmentation)."""

  def extract_section_department(segment: str) -> tuple[str | None, str | None]:
      """Extract section/structure/department from one segment. Returns (value, evidence)."""
  ```
- **Test:** (manual verification — covered by `test_contract_type.py` integration in 5.15 and row_builder behaviour in 5.16; no dedicated test file in `plan_implementation.md` for metadata)
- **Notes:**
  - `extract_pdf_call_title`: search the full pre-segmented text for a bando title line — typically the first meaningful non-blank line or a line matching a title pattern. Return `None` if not found.
  - `extract_section_department`: look for patterns like `"Sezione di X"`, `"Sede di X"`, `"Struttura di X"` (era variants per plan_desiderata). Return `(matched_string, evidence_snippet)` where evidence is the raw line. Return `(None, None)` if not found.
  - Section label variants (from plan_desiderata): `Sezione di X` / `Sede di X` / just `X` (standalone department name). Handle all known variants.
  - Pure text processing — no I/O, no imports from other `infn_jobs` modules.

[ ] done

**Substep 5.10 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.11 Field extractor: `contract_type.py`

### 5.11.1 Create `src/infn_jobs/extract/parse/fields/contract_type.py`
- **File:** `src/infn_jobs/extract/parse/fields/contract_type.py`
- **Action:** Create
- **Write:**
  ```python
  def extract_contract_type(segment: str, anno: int | None) -> dict:
      """Extract contract type, type_raw, and subtype fields from a segment.

      Returns dict with keys: contract_type, contract_type_raw, contract_type_evidence,
      contract_subtype, contract_subtype_raw, contract_subtype_evidence.
      All values are str | None.
      """
  ```
- **Test:** `pytest tests/extract/fields/test_contract_type.py -v` (test written in sub-substep 5.15.1)
- **Notes:**
  - `contract_type`: match known type keywords (case-insensitive): `borsa` → `"Borsa di studio"`, `contratto di ricerca` → `"Contratto di ricerca"`, `incarico di ricerca` → `"Incarico di ricerca"`, `incarico post.?doc` → `"Incarico Post-Doc"`, `assegno di ricerca` → `"Assegno di ricerca"`. Return `None` if nothing matched.
  - `contract_type_raw`: the original contract-type text as found in the PDF body (e.g., `"CONTRATTO DI RICERCA"`, `"BORSA DI STUDIO"`). Stored as-is before normalization. `None` if no contract type matched.
  - `contract_subtype_raw`: the raw subtype text as found in the PDF (e.g., `"Tipo A"`, `"Fascia II"`, `"Fascia 2"`).
  - `contract_subtype`: call `normalize_subtype(raw, anno)` from `infn_jobs.extract.parse.normalize.subtypes`.
  - Era gating for `Tipo A/B`: passed through `normalize_subtype`, which handles the `anno < 2010 → None` rule.
  - `*_evidence`: the raw text snippet (full matched line) that yielded each extracted value. `None` if the field was not found.
  - Pure regex/string processing on `segment`. No I/O.

[ ] done

**Substep 5.11 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.12 Field extractor: `duration.py`

### 5.12.1 Create `src/infn_jobs/extract/parse/fields/duration.py`
- **File:** `src/infn_jobs/extract/parse/fields/duration.py`
- **Action:** Create
- **Write:**
  ```python
  def extract_duration(segment: str) -> tuple[int | None, str | None, str | None]:
      """Extract duration from a segment. Returns (duration_months, duration_raw, evidence)."""
  ```
- **Test:** `pytest tests/extract/fields/test_duration.py -v` (test written in sub-substep 5.15.2)
- **Notes:**
  - Era label variants (per plan_desiderata): `Durata:` / `Periodo:` / `per la durata di` / `della durata di`. All map to the same extraction logic.
  - Numeric duration: `"12 mesi"` → `12`; `"24 mesi"` → `24`.
  - Word-based durations: `"biennale"` → `24`; `"triennale"` → `36`; `"annuale"` or `"annuo"` → `12`.
  - Parenthetical: `"24 (venti quattro) mesi"` → `24` (use the leading number).
  - `duration_raw`: the matched string before normalization (e.g., `"12 mesi"`, `"biennale"`).
  - `evidence`: the full matched line.
  - Return `(None, None, None)` if not found.
  - Pure regex/string processing on `segment`. No I/O.

[ ] done

**Substep 5.12 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.13 Field extractor: `income.py`

### 5.13.1 Create `src/infn_jobs/extract/parse/fields/income.py`
- **File:** `src/infn_jobs/extract/parse/fields/income.py`
- **Action:** Create
- **Write:**
  ```python
  def extract_income(segment: str) -> dict:
      """Extract all 7 EUR income/cost fields and 3 evidence fields from a segment.

      Returns dict with keys: institute_cost_total_eur, institute_cost_yearly_eur,
      gross_income_total_eur, gross_income_yearly_eur, net_income_total_eur,
      net_income_yearly_eur, net_income_monthly_eur, institute_cost_evidence,
      gross_income_evidence, net_income_evidence.
      All values are float | None (EUR fields) or str | None (evidence fields).
      """
  ```
- **Test:** `pytest tests/extract/fields/test_income.py -v` (test written in sub-substep 5.15.3)
- **Notes:**
  - Era label variants for gross income (from plan_desiderata): `Compenso lordo` / `Importo lordo` / `Reddito lordo` / `Retribuzione lorda`. All map to `gross_income_*` fields.
  - `institute_cost_*` labels: `Costo a carico dell'Ente` / `Costo istituzionale`.
  - `net_income_*` labels: `Compenso netto` / `Importo netto` / `Reddito netto`.
  - Total vs. yearly vs. monthly: distinguish via `totale` / `annuo` / `mensile` qualifiers on the same label line.
  - Call `normalize_eur()` from `infn_jobs.extract.parse.normalize.currency` to convert matched amount strings to float.
  - Return all `None` values (not `0.0`) if a field is not found. Per CLAUDE.md: "NULL EUR fields in old records are correct data — do not default to `0.0`."
  - Evidence: the raw matched line for each group (one evidence field per group: institute_cost, gross_income, net_income).
  - Pure regex/string processing on `segment`. No I/O.

[ ] done

**Substep 5.13 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.14 Field extractor: `confidence.py`

### 5.14.1 Create `src/infn_jobs/extract/parse/fields/confidence.py`
- **File:** `src/infn_jobs/extract/parse/fields/confidence.py`
- **Action:** Create
- **Write:**
  ```python
  def score_confidence(row: PositionRow, text_quality: str) -> ParseConfidence:
      """Compute parse_confidence for a PositionRow based on parsed fields and text quality."""
  ```
- **Test:** `pytest tests/extract/fields/test_confidence.py -v` (test written in sub-substep 5.17.1)
- **Notes:**
  - Import `PositionRow` from `infn_jobs.domain.position`; `ParseConfidence`, `TextQuality` from `infn_jobs.domain.enums`.
  - Rubric (per plan_desiderata):
    - `ParseConfidence.HIGH`: `row.duration_months is not None` **and** at least one of the 7 EUR fields is not `None`.
    - `ParseConfidence.MEDIUM`: `row.contract_type is not None` but all 7 EUR fields are `None`.
    - `ParseConfidence.LOW`: `text_quality` is `"ocr_degraded"` or `"no_text"`; OR all of `contract_type`, `duration_months`, and all EUR fields are `None` from readable text.
  - `text_quality` is passed as a `str` (the stored value, e.g., `"ocr_degraded"`) — compare against `TextQuality` enum values using `.value`.
  - Per CLAUDE.md: "`parse_confidence` is behavioral only — it reflects parser success, not data availability. NULL EUR fields in old records do not lower confidence." → A record with `contract_type` parsed but no EUR fields (because financial data was not publicly disclosed) correctly gets `MEDIUM`, not `LOW`.

[ ] done

**Substep 5.14 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.15 Field extractor tests

### 5.15.1 Create `tests/extract/fields/test_contract_type.py`
- **File:** `tests/extract/fields/test_contract_type.py`
- **Action:** Create
- **Write:**
  `test_extract_contract_type_contratto_ricerca`,
  `test_extract_contract_type_borsa`,
  `test_extract_contract_type_assegno_tipo_a_post2010`,
  `test_extract_contract_type_assegno_tipo_b_post2010`,
  `test_extract_contract_type_assegno_pre2010_subtype_is_none`,
  `test_extract_contract_type_fascia_ii_normalized_to_fascia_2`,
  `test_extract_contract_type_missing_returns_all_none`,
  `test_extract_contract_type_evidence_captured`
- **Test:** `pytest tests/extract/fields/test_contract_type.py -v`
- **Notes:**
  - Uses fixtures: `single_contract.txt` (→ contract_type = "Contratto di ricerca"), `assegno_tipo_ab.txt` (→ Tipo A and Tipo B), `assegno_old.txt` (→ subtype = None for anno=2007), `missing_fields.txt` (→ contract_type = "Borsa di studio").
  - Load each fixture and call `extract_contract_type(segment, anno)` on the first/only segment.
  - `test_extract_contract_type_fascia_ii_normalized_to_fascia_2`: use an inline segment string `"INCARICO DI RICERCA\nFascia II\nDurata: 12 mesi"` with `anno=2015` — assert `result["contract_subtype"] == "Fascia 2"` and `result["contract_subtype_raw"] == "Fascia II"`.
  - `test_extract_contract_type_assegno_pre2010_subtype_is_none`: load `assegno_old.txt`, call with `anno=2007` — assert `result["contract_subtype"] is None`.

[ ] done

### 5.15.2 Create `tests/extract/fields/test_duration.py`
- **File:** `tests/extract/fields/test_duration.py`
- **Action:** Create
- **Write:**
  `test_extract_duration_mesi_label`,
  `test_extract_duration_biennale`,
  `test_extract_duration_triennale`,
  `test_extract_duration_era_variant_della_durata_di`,
  `test_extract_duration_era_variant_periodo`,
  `test_extract_duration_parenthetical_number`,
  `test_extract_duration_missing_returns_triple_none`,
  `test_extract_duration_evidence_captured`
- **Test:** `pytest tests/extract/fields/test_duration.py -v`
- **Notes:**
  - Uses fixture `single_contract.txt` (→ duration_months = 12) and inline segment strings for era variant tests.
  - `test_extract_duration_era_variant_della_durata_di`: inline `"della durata di 24 mesi"` → `(24, "24 mesi", <evidence>)`.
  - `test_extract_duration_era_variant_periodo`: inline `"Periodo: 12 mesi"` → `(12, "12 mesi", <evidence>)`.
  - `test_extract_duration_parenthetical_number`: inline `"Durata: 24 (venti quattro) mesi"` → `(24, "24 (venti quattro) mesi", <evidence>)`.
  - `test_extract_duration_missing_returns_triple_none`: inline `"BORSA DI STUDIO\nSezione di Bari"` → `(None, None, None)`.

[ ] done

### 5.15.3 Create `tests/extract/fields/test_income.py`
- **File:** `tests/extract/fields/test_income.py`
- **Action:** Create
- **Write:**
  `test_extract_income_all_7_fields_from_fixture`,
  `test_extract_income_compenso_lordo_label`,
  `test_extract_income_importo_lordo_label`,
  `test_extract_income_reddito_lordo_label`,
  `test_extract_income_missing_financial_fields_all_none`,
  `test_extract_income_evidence_captured`,
  `test_extract_income_eur_fields_are_float_or_none`
- **Test:** `pytest tests/extract/fields/test_income.py -v`
- **Notes:**
  - Uses fixture `single_contract.txt` for `test_extract_income_all_7_fields_from_fixture` — assert `gross_income_yearly_eur == pytest.approx(28000.0)` and at least 4 EUR fields are non-None.
  - Uses fixture `missing_fields.txt` for `test_extract_income_missing_financial_fields_all_none` — assert all 7 EUR fields are `None`.
  - `test_extract_income_importo_lordo_label` and `test_extract_income_reddito_lordo_label`: use inline segment strings with those era-variant labels — assert they map to `gross_income_*` fields.
  - `test_extract_income_eur_fields_are_float_or_none`: call with any fixture and assert all 7 EUR keys in the result are either `float` or `None`.

[ ] done

**Substep 5.15 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/fields/ -v` passes with no failures.

---

## 5.16 Row builder

### 5.16.1 Create `src/infn_jobs/extract/parse/row_builder.py`
- **File:** `src/infn_jobs/extract/parse/row_builder.py`
- **Action:** Create
- **Write:**
  ```python
  def build_rows(
      text: str,
      detail_id: str,
      text_quality: str,
      anno: int | None,
  ) -> tuple[list[PositionRow], str | None]:
      """Segment text and build PositionRow list. Second element is pdf_call_title (call-level)."""
  ```
- **Test:** `pytest tests/extract/test_row_builder.py -v` (test written in sub-substep 5.18.1)
- **Notes:**
  - Per CLAUDE.md: "`build_rows` return type: `tuple[list[PositionRow], str | None]`. The second element is `pdf_call_title` (call-level, from the PDF body). The pipeline (`run_sync`) unpacks it, sets `call.pdf_call_title`, then calls `upsert_call`. Never store `pdf_call_title` inside `PositionRow`."
  - Algorithm:
    1. Call `extract_pdf_call_title(text)` on the full text → `pdf_call_title`.
    2. Call `segment(text)` → `segments: list[str]`.
    3. For each `(i, segment)` in `enumerate(segments)`:
       - Call all field extractors: `extract_contract_type`, `extract_duration`, `extract_income`, `extract_section_department`.
       - Assemble a `PositionRow` with `detail_id=detail_id`, `position_row_index=i`, `text_quality=text_quality`, and all extracted fields.
       - Call `score_confidence(row, text_quality)` and set `row.parse_confidence`.
    4. Return `(rows, pdf_call_title)`.
  - If `text` is empty or `text_quality` is `"no_text"`, return `([], None)`. Per CLAUDE.md: "`no_text` means mutool succeeded but extracted nothing. Produce 0 `position_rows`." No rows means no `parse_confidence` to assign.
  - If `text_quality` is `"ocr_degraded"`, still attempt segmentation and extraction — the extractors will return `None` for most fields, and `score_confidence` will assign `low`. Do not short-circuit for `ocr_degraded`.
  - Per CLAUDE.md: "`position_row_index` is 0-based, assigned by order of appearance in `segment()` output. Deterministic for identical PDF text. Never reorder."
  - **`text_quality` type:** `build_rows` receives `text_quality` as a `str` (the `.value` of the `TextQuality` enum). The pipeline (Step 7) must convert: `text_quality = text_quality_enum.value` before calling `build_rows`. Store this string directly on `PositionRow.text_quality`.
  - Import from: `infn_jobs.extract.parse.segmenter`, `infn_jobs.extract.parse.fields.*`, `infn_jobs.domain.position`, `infn_jobs.domain.enums`.

[ ] done

**Substep 5.16 done when:** all sub-substeps above are `[x]` and
`pytest tests/ -v` passes with no failures.

---

## 5.17 Confidence scoring tests

### 5.17.1 Create `tests/extract/fields/test_confidence.py`
- **File:** `tests/extract/fields/test_confidence.py`
- **Action:** Create
- **Write:**
  `test_score_confidence_high_with_duration_and_income`,
  `test_score_confidence_medium_contract_type_only`,
  `test_score_confidence_low_ocr_degraded`,
  `test_score_confidence_low_all_none_from_readable`,
  `test_score_confidence_high_requires_duration_and_eur`,
  `test_score_confidence_medium_no_eur_fields`
- **Test:** `pytest tests/extract/fields/test_confidence.py -v`
- **Notes:**
  - Import `score_confidence` from `infn_jobs.extract.parse.fields.confidence`, `PositionRow` from `infn_jobs.domain.position`, `ParseConfidence` from `infn_jobs.domain.enums`.
  - All test data is inline — create `PositionRow` instances with specific fields set.
  - `test_score_confidence_high_with_duration_and_income`: `PositionRow(duration_months=12, gross_income_yearly_eur=28000.0)` + `text_quality="digital"` → `ParseConfidence.HIGH`.
  - `test_score_confidence_medium_contract_type_only`: `PositionRow(contract_type="Borsa")` + `text_quality="digital"` → `ParseConfidence.MEDIUM`.
  - `test_score_confidence_low_ocr_degraded`: `PositionRow(contract_type="Borsa", duration_months=12)` + `text_quality="ocr_degraded"` → `ParseConfidence.LOW`.
  - `test_score_confidence_low_all_none_from_readable`: `PositionRow()` + `text_quality="digital"` → `ParseConfidence.LOW`.
  - `test_score_confidence_high_requires_duration_and_eur`: `PositionRow(duration_months=12)` (no EUR fields) + `text_quality="digital"` → NOT `HIGH` (verify it's `MEDIUM` or `LOW` depending on `contract_type`).
  - `test_score_confidence_medium_no_eur_fields`: `PositionRow(contract_type="Contratto di ricerca", duration_months=24)` (no EUR) + `text_quality="digital"` → `ParseConfidence.MEDIUM` (contract_type present but no EUR → medium, even though duration is present).

[ ] done

**Substep 5.17 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/fields/test_confidence.py -v` passes with no failures.

---

## 5.18 Row builder tests

### 5.18.1 Create `tests/extract/test_row_builder.py`
- **File:** `tests/extract/test_row_builder.py`
- **Action:** Create
- **Write:**
  `test_build_rows_single_contract_returns_one_row`,
  `test_build_rows_multi_same_type_returns_multiple_rows`,
  `test_build_rows_returns_pdf_call_title`,
  `test_build_rows_no_text_returns_empty`,
  `test_build_rows_empty_text_returns_empty`,
  `test_build_rows_position_row_index_sequential`,
  `test_build_rows_text_quality_stored_as_string`
- **Test:** `pytest tests/extract/test_row_builder.py -v`
- **Notes:**
  - Import `build_rows` from `infn_jobs.extract.parse.row_builder`.
  - Uses fixtures: `single_contract.txt`, `multi_same_type.txt`, `missing_fields.txt`.
  - `test_build_rows_single_contract_returns_one_row`: load `single_contract.txt`, call `build_rows(text, "test-1", "digital", 2022)` → assert `len(rows) == 1`.
  - `test_build_rows_multi_same_type_returns_multiple_rows`: load `multi_same_type.txt` → assert `len(rows) == 2`.
  - `test_build_rows_returns_pdf_call_title`: assert second element of return tuple is `str | None` (not an exception).
  - `test_build_rows_no_text_returns_empty`: call `build_rows("", "test-1", "no_text", 2022)` → assert `rows == []` and `pdf_call_title is None`.
  - `test_build_rows_empty_text_returns_empty`: call `build_rows("", "test-1", "digital", 2022)` → assert `rows == []`.
  - `test_build_rows_position_row_index_sequential`: load `multi_same_type.txt` → assert `rows[0].position_row_index == 0` and `rows[1].position_row_index == 1`.
  - `test_build_rows_text_quality_stored_as_string`: call with `text_quality="digital"` → assert `rows[0].text_quality == "digital"` (string, not enum).

[ ] done

**Substep 5.18 done when:** all sub-substeps above are `[x]` and
`pytest tests/extract/test_row_builder.py -v` passes with no failures.

---

## Verification

```bash
pytest tests/extract/ -v
ruff check src/infn_jobs/extract/
```

Expected: all extract layer tests green, ruff exits 0.

Manual checks:
- `python3 -c "from infn_jobs.extract.pdf.downloader import download; from infn_jobs.extract.pdf.mutool import extract_text; from infn_jobs.extract.parse.row_builder import build_rows; print('extract OK')"` prints `extract OK`.
- `python3 -c "from infn_jobs.extract.parse.normalize.currency import normalize_eur; assert normalize_eur('33.681,30') == 33681.30; print('currency OK')"` prints `currency OK`.
- `python3 -c "from infn_jobs.extract.parse.normalize.subtypes import normalize_subtype; assert normalize_subtype('Tipo A', 2008) is None; assert normalize_subtype('Tipo A', 2015) == 'Tipo A'; print('subtypes OK')"` prints `subtypes OK`.
