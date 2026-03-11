# Function and Class Index

> **Location:** `docs/info_functions.md`  
> **Auto-generated** by `scripts/gen_info_functions.py` — do not edit by hand.  
> Re-run whenever public functions are added, renamed, or removed:
> `python3 scripts/gen_info_functions.py`

Fields per entry: `name | parent | inputs | output | description`

## `src/infn_jobs/cli/cmd_export.py`
- `execute` | `infn_jobs.cli.cmd_export` | `args: argparse.Namespace` | `None` | Open DB, rebuild curated tables, export 4 CSVs, close DB.

## `src/infn_jobs/cli/cmd_sync.py`
- `execute` | `infn_jobs.cli.cmd_sync` | `args: argparse.Namespace` | `None` | Open DB, run full sync pipeline, close DB.

## `src/infn_jobs/cli/main.py`
- `build_parser` | `infn_jobs.cli.main` | — | `argparse.ArgumentParser` | Build and return the argument parser with all subcommands registered.
- `run` | `infn_jobs.cli.main` | — | `None` | Configure logging, parse arguments, and dispatch to the selected subcommand.

## `src/infn_jobs/cli/update_check.py`
- `UpdateInfo` | `infn_jobs.cli.update_check` | — | — | Local/remote commit information for the current branch.
- `check_for_github_update` | `infn_jobs.cli.update_check` | `project_root: Path` | `UpdateInfo | None` | Return update info when the remote branch differs from local HEAD.
- `maybe_handle_startup_update_check` | `infn_jobs.cli.update_check` | `project_root: Path` | `bool` | Run best-effort update check and prompt the user when needed.

## `src/infn_jobs/config/settings.py`
- `init_data_dirs` | `infn_jobs.config.settings` | — | `None` | Create data subdirectories if they do not exist. Idempotent.

## `src/infn_jobs/domain/call.py`
- `CallRaw` | `infn_jobs.domain.call` | — | — | All fields scraped for a single INFN job call; every field is nullable.

## `src/infn_jobs/domain/enums.py`
- `ListingStatus` | `infn_jobs.domain.enums` | — | — | Whether a job listing is currently active or has expired.
- `ContractType` | `infn_jobs.domain.enums` | — | — | The five INFN job source tipos, stored verbatim as they appear on the site.
- `ParseConfidence` | `infn_jobs.domain.enums` | — | — | Parser confidence in the extracted field values for a position row.
- `TextQuality` | `infn_jobs.domain.enums` | — | — | Classification of the PDF text source quality.

## `src/infn_jobs/domain/position.py`
- `PositionRow` | `infn_jobs.domain.position` | — | — | One contract line extracted from a PDF; every field is nullable.

## `src/infn_jobs/extract/parse/fields/confidence.py`
- `score_confidence` | `infn_jobs.extract.parse.fields.confidence` | `row: PositionRow`, `text_quality: str` | `ParseConfidence` | Compute parse_confidence for a PositionRow based on parsed fields and text quality.

## `src/infn_jobs/extract/parse/fields/contract_type.py`
- `extract_contract_type` | `infn_jobs.extract.parse.fields.contract_type` | `segment: str`, `anno: int | None` | `dict` | Extract contract type, type_raw, and subtype fields from a segment.

## `src/infn_jobs/extract/parse/fields/duration.py`
- `extract_duration` | `infn_jobs.extract.parse.fields.duration` | `segment: str` | `tuple[int | None, str | None, str | None]` | Extract duration from a segment. Returns (duration_months, duration_raw, evidence).

## `src/infn_jobs/extract/parse/fields/income.py`
- `extract_income` | `infn_jobs.extract.parse.fields.income` | `segment: str` | `dict` | Extract all 7 EUR income/cost fields and 3 evidence fields from a segment.

## `src/infn_jobs/extract/parse/fields/metadata.py`
- `extract_pdf_call_title` | `infn_jobs.extract.parse.fields.metadata` | `text: str` | `str | None` | Extract call-level title from full PDF text (before segmentation).
- `extract_section_department` | `infn_jobs.extract.parse.fields.metadata` | `segment: str` | `tuple[str | None, str | None]` | Extract section/structure/department from one segment. Returns (value, evidence).

## `src/infn_jobs/extract/parse/normalize/currency.py`
- `normalize_eur` | `infn_jobs.extract.parse.normalize.currency` | `s: str | None` | `float | None` | Normalize Italian-format EUR string to float. Returns None if unparseable.

## `src/infn_jobs/extract/parse/normalize/dates.py`
- `parse_date` | `infn_jobs.extract.parse.normalize.dates` | `s: str | None` | `date | None` | Parse a date string in DD-MM-YYYY or DD/MM/YYYY format. Returns None if invalid.

## `src/infn_jobs/extract/parse/normalize/subtypes.py`
- `normalize_subtype` | `infn_jobs.extract.parse.normalize.subtypes` | `s: str | None`, `anno: int | None` | `str | None` | Normalize contract subtype string to canonical form. Era-aware for Assegno subtypes.

## `src/infn_jobs/extract/parse/row_builder.py`
- `build_rows` | `infn_jobs.extract.parse.row_builder` | `text: str`, `detail_id: str`, `text_quality: str`, `anno: int | None` | `tuple[list[PositionRow], str | None]` | Segment text and build PositionRow list. Second element is pdf_call_title (call-level).

## `src/infn_jobs/extract/parse/segmenter.py`
- `segment` | `infn_jobs.extract.parse.segmenter` | `text: str` | `list[str]` | Split mutool text output into per-entry segments. Returns list with at least one element.

## `src/infn_jobs/extract/pdf/downloader.py`
- `download` | `infn_jobs.extract.pdf.downloader` | `url: str | None`, `dest: Path`, `session: requests.Session | None`, `force: bool` | `Path | None` | Download PDF to dest. Returns dest on success, None if url is None.

## `src/infn_jobs/extract/pdf/mutool.py`
- `extract_text` | `infn_jobs.extract.pdf.mutool` | `pdf_path: Path` | `tuple[str, TextQuality]` | Run mutool draw -F txt on pdf_path. Returns (text, text_quality).

## `src/infn_jobs/fetch/client.py`
- `get_session` | `infn_jobs.fetch.client` | — | `requests.Session` | Return a requests.Session with retry, backoff, and User-Agent configured.

## `src/infn_jobs/fetch/detail/parser.py`
- `parse_detail` | `infn_jobs.fetch.detail.parser` | `html: bytes`, `detail_id: str` | `CallRaw` | Parse a detail page and return a CallRaw with all available fields.

## `src/infn_jobs/fetch/listing/parser.py`
- `parse_rows` | `infn_jobs.fetch.listing.parser` | `html: bytes` | `list[dict]` | Parse a listing page and return one dict per call row.

## `src/infn_jobs/fetch/listing/url_builder.py`
- `build_urls` | `infn_jobs.fetch.listing.url_builder` | `tipo: str` | `list[str]` | Return [active_url, expired_url] for the given tipo string.

## `src/infn_jobs/fetch/orchestrator.py`
- `fetch_all_calls` | `infn_jobs.fetch.orchestrator` | `session: requests.Session`, `tipo: str`, `limit_per_tipo: int | None` | `list[CallRaw]` | Fetch calls for one tipo, optionally capped after combined active+expired ordering.

## `src/infn_jobs/pipeline/export.py`
- `run_export` | `infn_jobs.pipeline.export` | `conn: sqlite3.Connection`, `export_dir: Path` | `None` | Rebuild curated tables, then export all 4 CSVs to export_dir.

## `src/infn_jobs/pipeline/sync.py`
- `run_sync` | `infn_jobs.pipeline.sync` | `conn: sqlite3.Connection`, `source: str`, `limit_per_tipo: int | None`, `download_only: bool`, `dry_run: bool`, `force_refetch: bool` | `None` | Full idempotent sync pipeline: fetch all calls → extract PDFs → store.

## `src/infn_jobs/store/export/csv_writer.py`
- `export_all` | `infn_jobs.store.export.csv_writer` | `conn: sqlite3.Connection`, `export_dir: Path` | `None` | Write 4 CSV files to export_dir from all 4 DB tables.

## `src/infn_jobs/store/export/curate.py`
- `rebuild_curated` | `infn_jobs.store.export.curate` | `conn: sqlite3.Connection` | `None` | Rebuild calls_curated from the employment-like filter.

## `src/infn_jobs/store/read.py`
- `list_calls_for_pdf_processing` | `infn_jobs.store.read` | `conn: sqlite3.Connection` | `list[CallRaw]` | Return calls with detail_id set, ordered deterministically for PDF processing.

## `src/infn_jobs/store/schema.py`
- `init_db` | `infn_jobs.store.schema` | `conn: sqlite3.Connection` | `None` | Create 3 tables and 1 view with IF NOT EXISTS. Idempotent.

## `src/infn_jobs/store/spec/sql_parts.py`
- `comma_separated` | `infn_jobs.store.spec.sql_parts` | `items: tuple[str, ...]` | `str` | Join items with a comma+space separator preserving order.
- `named_placeholders` | `infn_jobs.store.spec.sql_parts` | `column_names: tuple[str, ...]` | `str` | Return SQLite named placeholders for column_names preserving order.
- `excluded_assignments` | `infn_jobs.store.spec.sql_parts` | `column_names: tuple[str, ...]`, `indent: str` | `str` | Return ON CONFLICT assignment lines using excluded.<column> values.
- `render_column_definition` | `infn_jobs.store.spec.sql_parts` | `column: ColumnSpec` | `str` | Render one column definition for CREATE TABLE statements.
- `render_table_body` | `infn_jobs.store.spec.sql_parts` | `spec: TableSpec`, `indent: str` | `str` | Render CREATE TABLE body lines for columns and constraints.
- `render_view_select_list` | `infn_jobs.store.spec.sql_parts` | `spec: ViewSpec`, `indent: str` | `str` | Render SELECT projection lines with explicit aliases.

## `src/infn_jobs/store/spec/types.py`
- `ColumnSpec` | `infn_jobs.store.spec.types` | — | — | Describe one table column in storage specs.
- `TableSpec` | `infn_jobs.store.spec.types` | — | — | Describe one SQLite table in storage specs.
- `column_names` | `TableSpec` | — | `tuple[str, ...]` | Return ordered column names for this table.
- `ViewColumnSpec` | `infn_jobs.store.spec.types` | — | — | Describe one output column in a SQLite view.
- `ViewSpec` | `infn_jobs.store.spec.types` | — | — | Describe one SQLite view projection in storage specs.
- `column_names` | `ViewSpec` | — | `tuple[str, ...]` | Return ordered output column names for this view.

## `src/infn_jobs/store/upsert.py`
- `upsert_call` | `infn_jobs.store.upsert` | `conn: sqlite3.Connection`, `call: CallRaw` | `None` | Upsert a CallRaw into calls_raw. Preserves first_seen_at on update.
- `upsert_position_rows` | `infn_jobs.store.upsert` | `conn: sqlite3.Connection`, `rows: list[PositionRow]` | `None` | Replace all position_rows for one detail_id batch; reject heterogeneous batches.
