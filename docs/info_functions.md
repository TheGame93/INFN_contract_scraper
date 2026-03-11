# Function and Class Index

> **Location:** `docs/info_functions.md`  
> **Auto-generated** by `scripts/gen_info_functions.py` — do not edit by hand.  
> Re-run whenever public functions are added, renamed, or removed:
> `python3 scripts/gen_info_functions.py`

---

### `execute`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/cli/cmd_export.py` |
| **Name** | `execute` |
| **Parent** | `infn_jobs.cli.cmd_export` |
| **Inputs** | `args: argparse.Namespace` |
| **Output** | `None` |
| **Description** | Open DB, rebuild curated tables, export 4 CSVs, close DB. |

---

### `execute`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/cli/cmd_sync.py` |
| **Name** | `execute` |
| **Parent** | `infn_jobs.cli.cmd_sync` |
| **Inputs** | `args: argparse.Namespace` |
| **Output** | `None` |
| **Description** | Open DB, run full sync pipeline, close DB. |

---

### `build_parser`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/cli/main.py` |
| **Name** | `build_parser` |
| **Parent** | `infn_jobs.cli.main` |
| **Inputs** | — |
| **Output** | `argparse.ArgumentParser` |
| **Description** | Build and return the argument parser with all subcommands registered. |

---

### `run`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/cli/main.py` |
| **Name** | `run` |
| **Parent** | `infn_jobs.cli.main` |
| **Inputs** | — |
| **Output** | `None` |
| **Description** | Configure logging, parse arguments, and dispatch to the selected subcommand. |

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

### `score_confidence`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/confidence.py` |
| **Name** | `score_confidence` |
| **Parent** | `infn_jobs.extract.parse.fields.confidence` |
| **Inputs** | `row: PositionRow`, `text_quality: str` |
| **Output** | `ParseConfidence` |
| **Description** | Compute parse_confidence for a PositionRow based on parsed fields and text quality. |

---

### `extract_contract_type`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/contract_type.py` |
| **Name** | `extract_contract_type` |
| **Parent** | `infn_jobs.extract.parse.fields.contract_type` |
| **Inputs** | `segment: str`, `anno: int | None` |
| **Output** | `dict` |
| **Description** | Extract contract type, type_raw, and subtype fields from a segment. |

---

### `extract_duration`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/duration.py` |
| **Name** | `extract_duration` |
| **Parent** | `infn_jobs.extract.parse.fields.duration` |
| **Inputs** | `segment: str` |
| **Output** | `tuple[int | None, str | None, str | None]` |
| **Description** | Extract duration from a segment. Returns (duration_months, duration_raw, evidence). |

---

### `extract_income`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/income.py` |
| **Name** | `extract_income` |
| **Parent** | `infn_jobs.extract.parse.fields.income` |
| **Inputs** | `segment: str` |
| **Output** | `dict` |
| **Description** | Extract all 7 EUR income/cost fields and 3 evidence fields from a segment. |

---

### `extract_pdf_call_title`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/metadata.py` |
| **Name** | `extract_pdf_call_title` |
| **Parent** | `infn_jobs.extract.parse.fields.metadata` |
| **Inputs** | `text: str` |
| **Output** | `str | None` |
| **Description** | Extract call-level title from full PDF text (before segmentation). |

---

### `extract_section_department`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/fields/metadata.py` |
| **Name** | `extract_section_department` |
| **Parent** | `infn_jobs.extract.parse.fields.metadata` |
| **Inputs** | `segment: str` |
| **Output** | `tuple[str | None, str | None]` |
| **Description** | Extract section/structure/department from one segment. Returns (value, evidence). |

---

### `normalize_eur`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/normalize/currency.py` |
| **Name** | `normalize_eur` |
| **Parent** | `infn_jobs.extract.parse.normalize.currency` |
| **Inputs** | `s: str | None` |
| **Output** | `float | None` |
| **Description** | Normalize Italian-format EUR string to float. Returns None if unparseable. |

---

### `parse_date`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/normalize/dates.py` |
| **Name** | `parse_date` |
| **Parent** | `infn_jobs.extract.parse.normalize.dates` |
| **Inputs** | `s: str | None` |
| **Output** | `date | None` |
| **Description** | Parse a date string in DD-MM-YYYY or DD/MM/YYYY format. Returns None if invalid. |

---

### `normalize_subtype`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/normalize/subtypes.py` |
| **Name** | `normalize_subtype` |
| **Parent** | `infn_jobs.extract.parse.normalize.subtypes` |
| **Inputs** | `s: str | None`, `anno: int | None` |
| **Output** | `str | None` |
| **Description** | Normalize contract subtype string to canonical form. Era-aware for Assegno subtypes. |

---

### `build_rows`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/row_builder.py` |
| **Name** | `build_rows` |
| **Parent** | `infn_jobs.extract.parse.row_builder` |
| **Inputs** | `text: str`, `detail_id: str`, `text_quality: str`, `anno: int | None` |
| **Output** | `tuple[list[PositionRow], str | None]` |
| **Description** | Segment text and build PositionRow list. Second element is pdf_call_title (call-level). |

---

### `segment`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/parse/segmenter.py` |
| **Name** | `segment` |
| **Parent** | `infn_jobs.extract.parse.segmenter` |
| **Inputs** | `text: str` |
| **Output** | `list[str]` |
| **Description** | Split mutool text output into per-entry segments. Returns list with at least one element. |

---

### `download`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/pdf/downloader.py` |
| **Name** | `download` |
| **Parent** | `infn_jobs.extract.pdf.downloader` |
| **Inputs** | `url: str | None`, `dest: Path`, `session: requests.Session | None`, `force: bool` |
| **Output** | `Path | None` |
| **Description** | Download PDF to dest. Returns dest on success, None if url is None. |

---

### `extract_text`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/extract/pdf/mutool.py` |
| **Name** | `extract_text` |
| **Parent** | `infn_jobs.extract.pdf.mutool` |
| **Inputs** | `pdf_path: Path` |
| **Output** | `tuple[str, TextQuality]` |
| **Description** | Run mutool draw -F txt on pdf_path. Returns (text, text_quality). |

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
| **Inputs** | `session: requests.Session`, `tipo: str`, `limit_per_tipo: int | None` |
| **Output** | `list[CallRaw]` |
| **Description** | Fetch calls for one tipo, optionally capped after combined active+expired ordering. |

---

### `run_export`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/pipeline/export.py` |
| **Name** | `run_export` |
| **Parent** | `infn_jobs.pipeline.export` |
| **Inputs** | `conn: sqlite3.Connection`, `export_dir: Path` |
| **Output** | `None` |
| **Description** | Rebuild curated tables, then export all 4 CSVs to export_dir. |

---

### `run_sync`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/pipeline/sync.py` |
| **Name** | `run_sync` |
| **Parent** | `infn_jobs.pipeline.sync` |
| **Inputs** | `conn: sqlite3.Connection`, `source: str`, `limit_per_tipo: int | None`, `download_only: bool`, `dry_run: bool`, `force_refetch: bool` |
| **Output** | `None` |
| **Description** | Full idempotent sync pipeline: fetch all calls → extract PDFs → store. |

---

### `export_all`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/export/csv_writer.py` |
| **Name** | `export_all` |
| **Parent** | `infn_jobs.store.export.csv_writer` |
| **Inputs** | `conn: sqlite3.Connection`, `export_dir: Path` |
| **Output** | `None` |
| **Description** | Write 4 CSV files to export_dir from all 4 DB tables. |

---

### `rebuild_curated`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/export/curate.py` |
| **Name** | `rebuild_curated` |
| **Parent** | `infn_jobs.store.export.curate` |
| **Inputs** | `conn: sqlite3.Connection` |
| **Output** | `None` |
| **Description** | Rebuild calls_curated from the employment-like filter. |

---

### `list_calls_for_pdf_processing`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/read.py` |
| **Name** | `list_calls_for_pdf_processing` |
| **Parent** | `infn_jobs.store.read` |
| **Inputs** | `conn: sqlite3.Connection` |
| **Output** | `list[CallRaw]` |
| **Description** | Return calls with detail_id set, ordered deterministically for PDF processing. |

---

### `init_db`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/schema.py` |
| **Name** | `init_db` |
| **Parent** | `infn_jobs.store.schema` |
| **Inputs** | `conn: sqlite3.Connection` |
| **Output** | `None` |
| **Description** | Create 3 tables and 1 view with IF NOT EXISTS. Idempotent. |

---

### `comma_separated`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `comma_separated` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `items: tuple[str, ...]` |
| **Output** | `str` |
| **Description** | Join items with a comma+space separator preserving order. |

---

### `named_placeholders`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `named_placeholders` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `column_names: tuple[str, ...]` |
| **Output** | `str` |
| **Description** | Return SQLite named placeholders for column_names preserving order. |

---

### `excluded_assignments`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `excluded_assignments` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `column_names: tuple[str, ...]`, `indent: str` |
| **Output** | `str` |
| **Description** | Return ON CONFLICT assignment lines using excluded.<column> values. |

---

### `render_column_definition`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `render_column_definition` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `column: ColumnSpec` |
| **Output** | `str` |
| **Description** | Render one column definition for CREATE TABLE statements. |

---

### `render_table_body`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `render_table_body` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `spec: TableSpec`, `indent: str` |
| **Output** | `str` |
| **Description** | Render CREATE TABLE body lines for columns and constraints. |

---

### `render_view_select_list`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/sql_parts.py` |
| **Name** | `render_view_select_list` |
| **Parent** | `infn_jobs.store.spec.sql_parts` |
| **Inputs** | `spec: ViewSpec`, `indent: str` |
| **Output** | `str` |
| **Description** | Render SELECT projection lines with explicit aliases. |

---

### `ColumnSpec`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `ColumnSpec` |
| **Parent** | `infn_jobs.store.spec.types` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Describe one table column in storage specs. |

---

### `TableSpec`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `TableSpec` |
| **Parent** | `infn_jobs.store.spec.types` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Describe one SQLite table in storage specs. |

---

### `column_names`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `column_names` |
| **Parent** | `TableSpec` |
| **Inputs** | — |
| **Output** | `tuple[str, ...]` |
| **Description** | Return ordered column names for this table. |

---

### `ViewColumnSpec`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `ViewColumnSpec` |
| **Parent** | `infn_jobs.store.spec.types` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Describe one output column in a SQLite view. |

---

### `ViewSpec`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `ViewSpec` |
| **Parent** | `infn_jobs.store.spec.types` |
| **Inputs** | — |
| **Output** | — |
| **Description** | Describe one SQLite view projection in storage specs. |

---

### `column_names`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/spec/types.py` |
| **Name** | `column_names` |
| **Parent** | `ViewSpec` |
| **Inputs** | — |
| **Output** | `tuple[str, ...]` |
| **Description** | Return ordered output column names for this view. |

---

### `upsert_call`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/upsert.py` |
| **Name** | `upsert_call` |
| **Parent** | `infn_jobs.store.upsert` |
| **Inputs** | `conn: sqlite3.Connection`, `call: CallRaw` |
| **Output** | `None` |
| **Description** | Upsert a CallRaw into calls_raw. Preserves first_seen_at on update. |

---

### `upsert_position_rows`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/store/upsert.py` |
| **Name** | `upsert_position_rows` |
| **Parent** | `infn_jobs.store.upsert` |
| **Inputs** | `conn: sqlite3.Connection`, `rows: list[PositionRow]` |
| **Output** | `None` |
| **Description** | Replace all position_rows for rows[0].detail_id. Deletes existing rows first. |

