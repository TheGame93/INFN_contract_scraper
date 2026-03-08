# Function and Class Index

> **Location:** `docs/info_functions.md`  
> **Auto-generated** by `scripts/gen_info_functions.py` — do not edit by hand.  
> Re-run whenever public functions are added, renamed, or removed:
> `python3 scripts/gen_info_functions.py`

---

### `CallRaw`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/call.py` |
| **Name** | `CallRaw` |
| **Parent** | `infn_jobs.domain.call` |
| **Inputs** | — |
| **Output** | — |
| **Description** | All fields scraped for a single INFN job call; every field is nullable. |

---

### `ListingStatus`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/enums.py` |
| **Name** | `ListingStatus` |
| **Parent** | `infn_jobs.domain.enums` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Whether a job listing is currently active or has expired. |

---

### `ContractType`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/enums.py` |
| **Name** | `ContractType` |
| **Parent** | `infn_jobs.domain.enums` |
| **Inputs** | — |
| **Output** | — |
| **Description** | The five INFN job source tipos, stored verbatim as they appear on the site. |

---

### `ParseConfidence`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/enums.py` |
| **Name** | `ParseConfidence` |
| **Parent** | `infn_jobs.domain.enums` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Parser confidence in the extracted field values for a position row. |

---

### `TextQuality`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/enums.py` |
| **Name** | `TextQuality` |
| **Parent** | `infn_jobs.domain.enums` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Classification of the PDF text source quality. |

---

### `PositionRow`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/domain/position.py` |
| **Name** | `PositionRow` |
| **Parent** | `infn_jobs.domain.position` |
| **Inputs** | — |
| **Output** | — |
| **Description** | One contract line extracted from a PDF; every field is nullable. |

