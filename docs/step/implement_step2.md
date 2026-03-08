# Step 2 — Domain Layer

> **Location:** `docs/step/implement_step2.md`
> **Prerequisites:** Step 1 complete
> **Produces:**
> - `src/infn_jobs/domain/enums.py`
> - `src/infn_jobs/domain/call.py`
> - `src/infn_jobs/domain/position.py`
> - `tests/test_domain.py`

Note: `tests/test_domain.py` is not listed in `plan_implementation.md`'s test file tree
(which targets "~20 files" and is approximate). It is added here to satisfy the policy's
testing requirement for substep 2.4.

---

## 2.1 Enums (`ListingStatus`, `ContractType`, `ParseConfidence`, `TextQuality`)

### 2.1.1 Create `src/infn_jobs/domain/enums.py`
- **File:** `src/infn_jobs/domain/enums.py`
- **Action:** Create
- **Write:**
  ```python
  class ListingStatus(str, Enum): ...   # "active" | "expired"
  class ContractType(str, Enum): ...    # one value per source tipo (5 total)
  class ParseConfidence(str, Enum): ... # "high" | "medium" | "low"
  class TextQuality(str, Enum): ...     # "digital" | "ocr_clean" | "ocr_degraded" | "no_text"
  ```
- **Test:** `pytest tests/test_domain.py::test_listing_status_values tests/test_domain.py::test_parse_confidence_values tests/test_domain.py::test_text_quality_values tests/test_domain.py::test_contract_type_values -v` (test written in sub-substep 2.4.1)
- **Notes:**
  - Use `class X(str, Enum)` throughout so enum values serialize cleanly to/from SQLite TEXT columns without extra conversion.
  - `ListingStatus` values: `ACTIVE = "active"`, `EXPIRED = "expired"`.
  - `ContractType` values match the 5 source tipo strings verbatim: `BORSA = "Borsa"`, `INCARICO_RICERCA = "Incarico di ricerca"`, `INCARICO_POSTDOC = "Incarico Post-Doc"`, `CONTRATTO_RICERCA = "Contratto di ricerca"`, `ASSEGNO_RICERCA = "Assegno di ricerca"`. Verify these against live site in Step 3.3 before Step 4.
  - `ParseConfidence` values: `HIGH = "high"`, `MEDIUM = "medium"`, `LOW = "low"`.
  - `TextQuality` values: `DIGITAL = "digital"`, `OCR_CLEAN = "ocr_clean"`, `OCR_DEGRADED = "ocr_degraded"`, `NO_TEXT = "no_text"`.
  - Domain layer has **no imports from other `infn_jobs` modules** — only stdlib (`enum`).

[x] done

**Substep 2.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/test_domain.py -v` passes with no failures.

---

## 2.2 `CallRaw` dataclass

### 2.2.1 Create `src/infn_jobs/domain/call.py`
- **File:** `src/infn_jobs/domain/call.py`
- **Action:** Create
- **Write:**
  ```python
  @dataclass
  class CallRaw:
      detail_id: str | None = None
      source_tipo: str | None = None
      listing_status: str | None = None
      numero: str | None = None
      anno: str | None = None
      titolo: str | None = None
      pdf_call_title: str | None = None
      numero_posti_html: int | None = None
      data_bando: str | None = None
      data_scadenza: str | None = None
      detail_url: str | None = None
      pdf_url: str | None = None
      pdf_cache_path: str | None = None
      pdf_fetch_status: str | None = None
      first_seen_at: str | None = None
      last_synced_at: str | None = None
  ```
- **Test:** `pytest tests/test_domain.py::test_call_raw_all_none tests/test_domain.py::test_call_raw_with_detail_id -v` (test written in sub-substep 2.4.1)
- **Notes:**
  - Fields mirror the `calls_raw` DB schema exactly. **All fields are `None` by default** per CLAUDE.md key convention ("All fields are nullable — always").
  - `detail_id` is the PRIMARY KEY in the DB but is still `str | None` in the dataclass — DB-level constraints are enforced in the store layer, not the domain layer.
  - `numero_posti_html` is `int | None` (maps to INTEGER in schema).
  - `pdf_call_title` is a call-level field populated by the pipeline from `build_rows()` return value — it is NOT set by the fetch layer. See CLAUDE.md: "`build_rows` return type: `tuple[list[PositionRow], str | None]` — second element is `pdf_call_title`."
  - `listing_status` stores `"active"` or `"expired"` as plain strings. Enum `ListingStatus` may be used in application logic but the dataclass field is `str | None` to avoid coercion on read-back from SQLite.
  - Import only from stdlib: `from __future__ import annotations`, `from dataclasses import dataclass`.

[x] done

**Substep 2.2 done when:** all sub-substeps above are `[x]` and
`pytest tests/test_domain.py -v` passes with no failures.

---

## 2.3 `PositionRow` dataclass

### 2.3.1 Create `src/infn_jobs/domain/position.py`
- **File:** `src/infn_jobs/domain/position.py`
- **Action:** Create
- **Write:**
  ```python
  @dataclass
  class PositionRow:
      detail_id: str | None = None
      position_row_index: int | None = None
      text_quality: str | None = None
      contract_type: str | None = None
      contract_type_raw: str | None = None
      contract_subtype: str | None = None
      contract_subtype_raw: str | None = None
      duration_months: int | None = None
      duration_raw: str | None = None
      section_structure_department: str | None = None
      institute_cost_total_eur: float | None = None
      institute_cost_yearly_eur: float | None = None
      gross_income_total_eur: float | None = None
      gross_income_yearly_eur: float | None = None
      net_income_total_eur: float | None = None
      net_income_yearly_eur: float | None = None
      net_income_monthly_eur: float | None = None
      contract_type_evidence: str | None = None
      contract_subtype_evidence: str | None = None
      duration_evidence: str | None = None
      section_evidence: str | None = None
      institute_cost_evidence: str | None = None
      gross_income_evidence: str | None = None
      net_income_evidence: str | None = None
      parse_confidence: str | None = None
  ```
- **Test:** `pytest tests/test_domain.py::test_position_row_all_none tests/test_domain.py::test_position_row_with_index -v` (test written in sub-substep 2.4.1)
- **Notes:**
  - Fields mirror the `position_rows` DB schema exactly. **All fields are `None` by default.**
  - `position_row_index` is `int | None` (INTEGER in schema). The primary key is `(detail_id, position_row_index)` at DB level; no constraint is encoded in the dataclass.
  - EUR fields (`institute_cost_*`, `gross_income_*`, `net_income_*`) are `float | None` (REAL in schema). NULL EUR fields in old records are correct data — do not default to `0.0`.
  - `duration_months` is `int | None` (INTEGER).
  - `contract_type_raw` stores the original contract-type text found in the PDF body (e.g., `"CONTRATTO DI RICERCA"`). `contract_type` stores the normalized canonical form (e.g., `"Contratto di ricerca"`). Both are `str | None`.
  - `contract_subtype` stores the **canonical** form (e.g. `"Fascia 2"`, `"Tipo A"`, `"Tipo B"`). `contract_subtype_raw` stores the original text found in the PDF. Both are `str | None`.
  - `parse_confidence` stores `"high"` | `"medium"` | `"low"` as plain string. `text_quality` stores `"digital"` | `"ocr_clean"` | `"ocr_degraded"` | `"no_text"` as plain string.
  - `section_structure_department` is row-level — different rows in the same PDF may have different values. This is expected, not an error.
  - Import only from stdlib: `from __future__ import annotations`, `from dataclasses import dataclass`.

[x] done

**Substep 2.3 done when:** all sub-substeps above are `[x]` and
`pytest tests/test_domain.py -v` passes with no failures.

---

## 2.4 Domain smoke tests

### 2.4.1 Create `tests/test_domain.py`
- **File:** `tests/test_domain.py`
- **Action:** Create
- **Write:**
  `test_listing_status_values`, `test_contract_type_values`, `test_parse_confidence_values`,
  `test_text_quality_values`, `test_call_raw_all_none`, `test_call_raw_with_detail_id`,
  `test_call_raw_pdf_call_title_defaults_none`, `test_position_row_all_none`,
  `test_position_row_with_index`, `test_position_row_eur_fields_default_none`
- **Test:** `pytest tests/test_domain.py -v`
- **Notes:**
  - No fixture files needed — all test data is inline.
  - `test_listing_status_values`: assert `ListingStatus.ACTIVE.value == "active"` and `ListingStatus.EXPIRED.value == "expired"`.
  - `test_contract_type_values`: assert all 5 `ContractType` members exist and their `.value` strings match the 5 tipo names.
  - `test_parse_confidence_values`: assert `HIGH = "high"`, `MEDIUM = "medium"`, `LOW = "low"`.
  - `test_text_quality_values`: assert all 4 TextQuality values (`"digital"`, `"ocr_clean"`, `"ocr_degraded"`, `"no_text"`).
  - `test_call_raw_all_none`: `c = CallRaw()` — assert every field is `None` including `detail_id`, `pdf_call_title`, `numero_posti_html`.
  - `test_call_raw_with_detail_id`: `c = CallRaw(detail_id="123")` — assert `c.detail_id == "123"` and all other fields `None`.
  - `test_call_raw_pdf_call_title_defaults_none`: verify `CallRaw().pdf_call_title is None` (guards against accidental default).
  - `test_position_row_all_none`: `r = PositionRow()` — assert every field is `None` including all EUR fields and `position_row_index`.
  - `test_position_row_with_index`: `r = PositionRow(detail_id="42", position_row_index=0)` — assert values round-trip correctly.
  - `test_position_row_eur_fields_default_none`: assert each of the 7 EUR fields (`institute_cost_total_eur`, etc.) is `None` on a default `PositionRow()` — guards against accidental `0.0` defaults.

[x] done

**Substep 2.4 done when:** all sub-substeps above are `[x]` and
`pytest tests/test_domain.py -v` passes with no failures.

---

## Verification

```bash
pytest tests/test_domain.py -v
ruff check src/infn_jobs/domain/
```

Expected: all 10 tests green, ruff exits 0.

Manual: `python3 -c "from infn_jobs.domain.enums import ListingStatus, ContractType, ParseConfidence, TextQuality; from infn_jobs.domain.call import CallRaw; from infn_jobs.domain.position import PositionRow; print('domain OK')"` prints `domain OK`.
