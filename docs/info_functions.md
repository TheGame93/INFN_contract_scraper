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

## `src/infn_jobs/extract/parse/contracts/assegno_ricerca_profile.py`
- `build_profile` | `infn_jobs.extract.parse.contracts.assegno_ricerca_profile` | — | `ContractProfile` | Return profile metadata for Assegno di ricerca extraction rules.

## `src/infn_jobs/extract/parse/contracts/base_profile.py`
- `build_base_profile` | `infn_jobs.extract.parse.contracts.base_profile` | `canonical_name: str`, `aliases: tuple[str, ...]`, `contract_type_patterns: tuple[str, ...]`, `subtype_patterns: tuple[str, ...]`, `subtype_anno_min: int | None`, `subtype_anno_max: int | None` | `ContractProfile` | Return one contract profile with common baseline defaults applied.

## `src/infn_jobs/extract/parse/contracts/borsa_profile.py`
- `build_profile` | `infn_jobs.extract.parse.contracts.borsa_profile` | — | `ContractProfile` | Return profile metadata for Borsa di studio extraction rules.

## `src/infn_jobs/extract/parse/contracts/contratto_ricerca_profile.py`
- `build_profile` | `infn_jobs.extract.parse.contracts.contratto_ricerca_profile` | — | `ContractProfile` | Return profile metadata for Contratto di ricerca extraction rules.

## `src/infn_jobs/extract/parse/contracts/incarico_postdoc_profile.py`
- `build_profile` | `infn_jobs.extract.parse.contracts.incarico_postdoc_profile` | — | `ContractProfile` | Return profile metadata for Incarico Post-Doc extraction rules.

## `src/infn_jobs/extract/parse/contracts/incarico_ricerca_profile.py`
- `build_profile` | `infn_jobs.extract.parse.contracts.incarico_ricerca_profile` | — | `ContractProfile` | Return profile metadata for Incarico di ricerca extraction rules.

## `src/infn_jobs/extract/parse/contracts/profile.py`
- `ContractProfile` | `infn_jobs.extract.parse.contracts.profile` | — | — | Describe one contract family and its identifying aliases.

## `src/infn_jobs/extract/parse/contracts/registry.py`
- `list_profiles` | `infn_jobs.extract.parse.contracts.registry` | — | `tuple[ContractProfile, ...]` | Return all known contract profiles in deterministic order.
- `get_profile` | `infn_jobs.extract.parse.contracts.registry` | `canonical_name: str` | `ContractProfile | None` | Return profile for canonical_name, or None when unknown.
- `profile_alias_map` | `infn_jobs.extract.parse.contracts.registry` | — | `dict[str, str]` | Return alias -> canonical contract name mapping.

## `src/infn_jobs/extract/parse/core/classification.py`
- `classify_segment` | `infn_jobs.extract.parse.core.classification` | `segment_text: str` | `SegmentClassification` | Classify one segment into a contract family with deterministic tie-breaks.
- `classify_segments` | `infn_jobs.extract.parse.core.classification` | `spans: list[SegmentSpan]` | `list[SegmentClassification]` | Classify all segment spans in order.

## `src/infn_jobs/extract/parse/core/conflict_resolution.py`
- `candidate_sort_key` | `infn_jobs.extract.parse.core.conflict_resolution` | `candidate: RuleCandidate` | `tuple[int, str]` | Return a stable precedence key `(tier_rank, rule_id)` for one candidate.
- `choose_winner` | `infn_jobs.extract.parse.core.conflict_resolution` | `candidates: tuple[RuleCandidate, ...]` | `RuleCandidate | None` | Return deterministic winner candidate from a candidate set.
- `merge_execution_results` | `infn_jobs.extract.parse.core.conflict_resolution` | `results: tuple[ExecutionResult, ...]` | `ExecutionResult` | Merge execution results and resolve one deterministic winner.

## `src/infn_jobs/extract/parse/core/models.py`
- `ParseRequest` | `infn_jobs.extract.parse.core.models` | — | — | Input payload for one parser execution.
- `ParseResult` | `infn_jobs.extract.parse.core.models` | — | — | Output payload produced by one parser execution.
- `PreprocessResult` | `infn_jobs.extract.parse.core.models` | — | — | Normalized text plus source-line mapping for traceability.
- `SegmentSpan` | `infn_jobs.extract.parse.core.models` | — | — | One segmented text chunk with source-line boundaries.
- `SegmentClassification` | `infn_jobs.extract.parse.core.models` | — | — | Weighted contract-family classification for one segment.

## `src/infn_jobs/extract/parse/core/orchestrator.py`
- `run_parse_pipeline` | `infn_jobs.extract.parse.core.orchestrator` | `request: ParseRequest` | `ParseResult` | Build PositionRow values through the rule-driven parser pipeline.

## `src/infn_jobs/extract/parse/core/preprocess.py`
- `preprocess_text` | `infn_jobs.extract.parse.core.preprocess` | `text: str` | `PreprocessResult` | Normalize text while keeping a mapping to original line numbers.

## `src/infn_jobs/extract/parse/core/segmentation.py`
- `segment_preprocessed` | `infn_jobs.extract.parse.core.segmentation` | `preprocessed: PreprocessResult` | `list[SegmentSpan]` | Split preprocessed text into deterministic segment spans.

## `src/infn_jobs/extract/parse/diagnostics/collector.py`
- `EventCollector` | `infn_jobs.extract.parse.diagnostics.collector` | — | — | Collect parser events in insertion order.
- `record` | `EventCollector` | `event: ParseEvent` | `None` | Store one parser event.
- `snapshot` | `EventCollector` | — | `tuple[ParseEvent, ...]` | Return an immutable snapshot of recorded events.
- `record_winner` | `EventCollector` | `detail_id: str`, `field_name: str`, `candidate: RuleCandidate`, `source_line_start: int | None`, `source_line_end: int | None` | `None` | Record one winner event from rule execution.
- `record_rejected` | `EventCollector` | `detail_id: str`, `rejected: RejectedCandidate`, `source_line_start: int | None`, `source_line_end: int | None` | `None` | Record one rejected-candidate event from rule execution.

## `src/infn_jobs/extract/parse/diagnostics/events.py`
- `ParseEvent` | `infn_jobs.extract.parse.diagnostics.events` | — | — | Represent one parser diagnostic event.

## `src/infn_jobs/extract/parse/diagnostics/render.py`
- `render_events` | `infn_jobs.extract.parse.diagnostics.render` | `events: tuple[ParseEvent, ...]` | `str` | Return one deterministic text block for diagnostics events.

## `src/infn_jobs/extract/parse/diagnostics/review_mode.py`
- `SegmentReview` | `infn_jobs.extract.parse.diagnostics.review_mode` | — | — | Deterministic parse-review artifacts for one segment.
- `ParseReviewReport` | `infn_jobs.extract.parse.diagnostics.review_mode` | — | — | Deterministic parse-review payload for one detail_id case.
- `build_review_report` | `infn_jobs.extract.parse.diagnostics.review_mode` | `text: str`, `detail_id: str`, `text_quality: str`, `anno: int | None` | `ParseReviewReport` | Return deterministic parse-review artifacts from one mutool text payload.
- `render_review_report` | `infn_jobs.extract.parse.diagnostics.review_mode` | `report: ParseReviewReport` | `str` | Render one deterministic text block for parse-review artifacts.

## `src/infn_jobs/extract/parse/fields/confidence.py`
- `score_confidence` | `infn_jobs.extract.parse.fields.confidence` | `row: PositionRow` | `ParseConfidence` | Compute parse_confidence from extracted row outcomes and text_quality.

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

## `src/infn_jobs/extract/parse/rules/common.py`
- `priority_rank` | `infn_jobs.extract.parse.rules.common` | `tier: PriorityTier` | `int` | Return sortable priority rank for tier.
- `contract_filter_matches` | `infn_jobs.extract.parse.rules.common` | `rule: RuleDefinition`, `context: RuleContext` | `bool` | Return True when contract filter allows this context.
- `anno_filter_matches` | `infn_jobs.extract.parse.rules.common` | `rule: RuleDefinition`, `context: RuleContext` | `bool` | Return True when anno constraints allow this context.

## `src/infn_jobs/extract/parse/rules/contract_identity.py`
- `ContractIdentityResolution` | `infn_jobs.extract.parse.rules.contract_identity` | — | — | Resolved contract identity/subtype values plus underlying rule traces.
- `resolve_contract_identity` | `infn_jobs.extract.parse.rules.contract_identity` | `segment_text: str`, `anno: int | None`, `predicted_contract_type: str | None`, `detail_id: str` | `ContractIdentityResolution` | Resolve contract type/subtype fields via deterministic profile-aware rules.

## `src/infn_jobs/extract/parse/rules/duration.py`
- `DurationValue` | `infn_jobs.extract.parse.rules.duration` | — | — | One duration candidate value plus its raw snippet and evidence line.
- `DurationResolution` | `infn_jobs.extract.parse.rules.duration` | — | — | Resolved duration fields plus underlying rule execution trace.
- `resolve_duration` | `infn_jobs.extract.parse.rules.duration` | `segment_text: str`, `detail_id: str`, `anno: int | None`, `contract_type: str | None` | `DurationResolution` | Resolve duration fields via primary/fallback/guard rule groups.

## `src/infn_jobs/extract/parse/rules/duration_helpers.py`
- `iter_nonempty_lines` | `infn_jobs.extract.parse.rules.duration_helpers` | `text: str` | `tuple[str, ...]` | Return non-empty stripped lines preserving source order.
- `extract_labeled_value_text` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[str, str] | None` | Return `(value_text, evidence_line)` for the first labeled duration line.
- `extract_labeled_numeric` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for numeric labeled duration.
- `extract_labeled_one_month` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for labeled one-month duration.
- `extract_labeled_triennale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for labeled triennale duration.
- `extract_labeled_biennale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for labeled biennale duration.
- `extract_labeled_annuale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for labeled annuale/annuo duration.
- `extract_bare_triennale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for fallback triennale duration.
- `extract_bare_biennale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for fallback biennale duration.
- `extract_bare_annuale` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for fallback annuale/annuo duration.
- `extract_numeric_guarded` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `tuple[int, str, str] | None` | Return `(months, raw, evidence)` for guard-tier numeric duration.
- `has_duration_context` | `infn_jobs.extract.parse.rules.duration_helpers` | `segment_text: str` | `bool` | Return True when segment includes duration-like context words.

## `src/infn_jobs/extract/parse/rules/executor.py`
- `execute_rules` | `infn_jobs.extract.parse.rules.executor` | `rules: tuple[RuleDefinition, ...]`, `context: RuleContext` | `ExecutionResult` | Execute rules and return winner/candidates/rejected trace.

## `src/infn_jobs/extract/parse/rules/income.py`
- `IncomeAmount` | `infn_jobs.extract.parse.rules.income` | — | — | One parsed EUR amount candidate plus its evidence line.
- `IncomeResolution` | `infn_jobs.extract.parse.rules.income` | — | — | Resolved income fields and per-field execution traces.
- `resolve_income` | `infn_jobs.extract.parse.rules.income` | `segment_text: str`, `detail_id: str`, `anno: int | None`, `contract_type: str | None` | `IncomeResolution` | Resolve all income fields through rule-driven per-field adapters.

## `src/infn_jobs/extract/parse/rules/income_helpers.py`
- `iter_lines` | `infn_jobs.extract.parse.rules.income_helpers` | `segment_text: str` | `tuple[str, ...]` | Return non-empty stripped segment lines preserving source order.
- `extract_amount` | `infn_jobs.extract.parse.rules.income_helpers` | `line: str`, `start_pos: int` | `float | None` | Extract amount from one line using stable precedence patterns.
- `line_has_no_qualifier` | `infn_jobs.extract.parse.rules.income_helpers` | `line: str` | `bool` | Return True when line has no total/yearly/monthly qualifier token.
- `find_amount` | `infn_jobs.extract.parse.rules.income_helpers` | `segment_text: str`, `label_re: re.Pattern[str]`, `require_total: bool`, `require_yearly: bool`, `require_monthly: bool`, `require_no_qualifier: bool` | `tuple[float, str] | None` | Return last matching `(amount, evidence)` candidate for constraints.

## `src/infn_jobs/extract/parse/rules/models.py`
- `RuleContext` | `infn_jobs.extract.parse.rules.models` | — | — | Execution context passed to parser rules.
- `RuleDefinition` | `infn_jobs.extract.parse.rules.models` | — | — | Define one extraction rule and its evaluation constraints.
- `RuleCandidate` | `infn_jobs.extract.parse.rules.models` | — | — | One candidate value proposed by a parser rule.
- `RejectedCandidate` | `infn_jobs.extract.parse.rules.models` | — | — | One rejected candidate decision emitted by the executor.
- `ExecutionResult` | `infn_jobs.extract.parse.rules.models` | — | — | Deterministic executor output for one field resolution.

## `src/infn_jobs/extract/parse/rules/section.py`
- `SectionResolution` | `infn_jobs.extract.parse.rules.section` | — | — | Resolved section value/evidence plus underlying rule trace.
- `resolve_section` | `infn_jobs.extract.parse.rules.section` | `segment_text: str`, `detail_id: str`, `anno: int | None`, `contract_type: str | None` | `SectionResolution` | Resolve section/structure/department field via deterministic rules.

## `src/infn_jobs/extract/parse/segmenter.py`
- `segment` | `infn_jobs.extract.parse.segmenter` | `text: str` | `list[str]` | Split mutool text output into per-entry segments. Returns list with at least one element.

## `src/infn_jobs/extract/pdf/downloader.py`
- `download` | `infn_jobs.extract.pdf.downloader` | `url: str | None`, `dest: Path`, `session: requests.Session | None`, `force: bool` | `Path | None` | Download PDF to dest. Returns dest on success, None if url is None.

## `src/infn_jobs/extract/pdf/mutool.py`
- `extract_text` | `infn_jobs.extract.pdf.mutool` | `pdf_path: Path` | `tuple[str, TextQuality]` | Run mutool draw -F txt on pdf_path. Returns (text, text_quality).

## `src/infn_jobs/extract/pdf/text_quality.py`
- `classify_text_quality` | `infn_jobs.extract.pdf.text_quality` | `text: str` | `TextQuality` | Classify mutool-extracted text into one deterministic quality bucket.

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
