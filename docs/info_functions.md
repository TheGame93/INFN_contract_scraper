# Function and Class Index

> **Location:** `docs/info_functions.md`  
> **Auto-generated** by `scripts/gen_info_functions.py` — do not edit by hand.  
> Re-run whenever public functions are added, renamed, or removed:
> `python3 scripts/gen_info_functions.py`

---

### `init_data_dirs`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/config/settings.py` |
| **Name** | `init_data_dirs` |
| **Parent** | `infn_jobs.config.settings` |
| **Inputs** | — |
| **Output** | `None` |
| **Description** | Create data subdirectories if they do not exist. Idempotent. |

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

---

### `get_session`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/fetch/client.py` |
| **Name** | `get_session` |
| **Parent** | `infn_jobs.fetch.client` |
| **Inputs** | — |
| **Output** | `requests.Session` |
| **Description** | Return a requests.Session with retry, backoff, and User-Agent configured. |

---

### `parse_detail`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/fetch/detail/parser.py` |
| **Name** | `parse_detail` |
| **Parent** | `infn_jobs.fetch.detail.parser` |
| **Inputs** | `html: bytes`, `detail_id: str` |
| **Output** | `CallRaw` |
| **Description** | Parse a detail page and return a CallRaw with all available fields. |

---

### `parse_rows`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/fetch/listing/parser.py` |
| **Name** | `parse_rows` |
| **Parent** | `infn_jobs.fetch.listing.parser` |
| **Inputs** | `html: bytes` |
| **Output** | `list[dict]` |
| **Description** | Parse a listing page and return one dict per call row. |

---

### `build_urls`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/fetch/listing/url_builder.py` |
| **Name** | `build_urls` |
| **Parent** | `infn_jobs.fetch.listing.url_builder` |
| **Inputs** | `tipo: str` |
| **Output** | `list[str]` |
| **Description** | Return [active_url, expired_url] for the given tipo string. |

---

### `fetch_all_calls`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/fetch/orchestrator.py` |
| **Name** | `fetch_all_calls` |
| **Parent** | `infn_jobs.fetch.orchestrator` |
| **Inputs** | `session: requests.Session`, `tipo: str` |
| **Output** | `list[CallRaw]` |
| **Description** | Fetch all active and expired calls for one tipo. Returns assembled CallRaw list. |

