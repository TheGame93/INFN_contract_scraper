# Parsing Plan

This document tracks parsing progress field-by-field for the .db and each exported CSV.

## Data Flow Diagrams

### DB table/view dependencies

`calls_raw` is the source-of-truth table (one row per call).  
`calls_curated` is a filtered copy of `calls_raw` for analysis-ready call subsets.  
`position_rows` stores PDF-extracted rows (one call can generate multiple rows), linked by `detail_id`.  
`position_rows_curated` is a **view** (saved query, not stored data) that joins `position_rows` + `calls_curated` into one flat analytical dataset.

```text
calls_raw (table, PK: detail_id)
  |
  +--> calls_curated (table, PK: detail_id)
  |     (rebuilt by filter on source_tipo from calls_raw)
  |
  +--> position_rows (table, PK: detail_id + position_row_index)
        (FK: detail_id -> calls_raw.detail_id)

position_rows_curated (VIEW)
  = JOIN position_rows.detail_id = calls_curated.detail_id
```

### DB -> CSV dependencies

```text
calls_raw (table)           -> calls_raw.csv
calls_curated (table)       -> calls_curated.csv
position_rows (table)       -> position_rows_raw.csv
position_rows_curated (VIEW)-> position_rows_curated.csv
```


## infn_jobs.db

This SQLite DB has 3 physical tables and 1 analytical view:
- `calls_raw`
- `calls_curated`
- `position_rows`
- `position_rows_curated` (VIEW)

### calls_raw (table)

| field | status | comment and/or current behaviour |
|---|---|---|
| detail_id | ok | website record id (`dettagli_job.php?id=...`) |
| source_tipo | ok | listing category from HTML |
| listing_status | ok | `active` or `expired` |
| numero | ok | call number (e.g. `28306`) |
| anno | ok | call year |
| titolo | no | title to be parsed from the "dettaglio bando" table |
| pdf_call_title | set as optional | title parsed from PDF text (first non-empty line) |
| numero_posti_html | ok | number of positions from HTML detail page |
| data_bando | ok | publication date from HTML |
| data_scadenza | ok | deadline date from HTML |
| detail_url | ok | full detail page URL |
| pdf_url | ok | full PDF URL (nullable) |
| pdf_cache_path | ok | local cached PDF path |
| pdf_fetch_status | ok | `ok`, `download_error`, `parse_error`, `skipped` |
| first_seen_at | ok | first time this `detail_id` was inserted |
| last_synced_at | ok | last sync timestamp |

### calls_curated (table)

Calls_curated is a filtered copy of calls_raw with the same columns. It keeps only rows where source_tipo is in the employment-like set (Borsa, Incarico di ricerca, Incarico Post-Doc, Contratto di ricerca, Assegno di ricerca)

| field | status | comment |
|---|---|---|
| detail_id |  | same schema as `calls_raw` |
| source_tipo |  | same schema as `calls_raw` |
| listing_status |  | same schema as `calls_raw` |
| numero |  | same schema as `calls_raw` |
| anno |  | same schema as `calls_raw` |
| titolo |  | same schema as `calls_raw` |
| pdf_call_title |  | same schema as `calls_raw` |
| numero_posti_html |  | same schema as `calls_raw` |
| data_bando |  | same schema as `calls_raw` |
| data_scadenza |  | same schema as `calls_raw` |
| detail_url |  | same schema as `calls_raw` |
| pdf_url |  | same schema as `calls_raw` |
| pdf_cache_path |  | same schema as `calls_raw` |
| pdf_fetch_status |  | same schema as `calls_raw` |
| first_seen_at |  | same schema as `calls_raw` |
| last_synced_at |  | same schema as `calls_raw` |

### position_rows (table)

| field | status | comment |
|---|---|---|
| detail_id | ok | Foreign key (FK) that refers to `calls_raw.detail_id` |
| position_row_index | ok | row index inside one PDF (`0..N-1`), when a bando gave more type of positions |
| text_quality |  | `digital`, `ocr_clean`, `ocr_degraded`, `no_text` |
| contract_type |  | canonical contract type extracted from PDF |
| contract_type_raw |  | original matched type text |
| contract_subtype |  | canonical subtype (when available) |
| contract_subtype_raw |  | original matched subtype text |
| duration_months |  | parsed duration in months |
| duration_raw |  | original duration snippet |
| section_structure_department |  | parsed section/structure |
| institute_cost_total_eur |  | EUR value parsed from PDF |
| institute_cost_yearly_eur |  | EUR value parsed from PDF |
| gross_income_total_eur |  | EUR value parsed from PDF |
| gross_income_yearly_eur |  | EUR value parsed from PDF |
| net_income_total_eur |  | EUR value parsed from PDF |
| net_income_yearly_eur |  | EUR value parsed from PDF |
| net_income_monthly_eur |  | EUR value parsed from PDF |
| contract_type_evidence |  | evidence line used for `contract_type` |
| contract_subtype_evidence |  | evidence line used for `subtype` |
| duration_evidence |  | evidence line used for `duration` |
| section_evidence |  | evidence line used for `section` |
| institute_cost_evidence |  | evidence line used for `institute cost` |
| gross_income_evidence |  | evidence line used for `gross income` |
| net_income_evidence |  | evidence line used for `net income` |
| parse_confidence |  | `high`, `medium`, `low` |

### position_rows_curated (view)

| field | status | comment |
|---|---|---|
| detail_id |  | from `position_rows` |
| position_row_index |  | from `position_rows` |
| source_tipo |  | from `calls_curated` |
| listing_status |  | from `calls_curated` |
| numero |  | from `calls_curated` |
| anno |  | from `calls_curated` |
| numero_posti_html |  | from `calls_curated` |
| data_bando |  | from `calls_curated` |
| data_scadenza |  | from `calls_curated` |
| first_seen_at |  | from `calls_curated` |
| last_synced_at |  | from `calls_curated` |
| pdf_fetch_status |  | from `calls_curated` |
| detail_url |  | from `calls_curated` |
| pdf_url |  | from `calls_curated` |
| pdf_cache_path |  | from `calls_curated` |
| call_title |  | `COALESCE(pdf_call_title, titolo)` |
| text_quality |  | from `position_rows` |
| contract_type |  | from `position_rows` |
| contract_type_raw |  | from `position_rows` |
| contract_subtype |  | from `position_rows` |
| contract_subtype_raw |  | from `position_rows` |
| duration_months |  | from `position_rows` |
| duration_raw |  | from `position_rows` |
| section_structure_department |  | from `position_rows` |
| institute_cost_total_eur |  | from `position_rows` |
| institute_cost_yearly_eur |  | from `position_rows` |
| gross_income_total_eur |  | from `position_rows` |
| gross_income_yearly_eur |  | from `position_rows` |
| net_income_total_eur |  | from `position_rows` |
| net_income_yearly_eur |  | from `position_rows` |
| net_income_monthly_eur |  | from `position_rows` |
| contract_type_evidence |  | from `position_rows` |
| contract_subtype_evidence |  | from `position_rows` |
| duration_evidence |  | from `position_rows` |
| section_evidence |  | from `position_rows` |
| institute_cost_evidence |  | from `position_rows` |
| gross_income_evidence |  | from `position_rows` |
| net_income_evidence |  | from `position_rows` |
| parse_confidence |  | from `position_rows` |

## .csv files

### calls_raw.csv

One row is one call published on the INFN jobs site.
It keeps the original call info plus basic run status.

| field | status |
|---|---|
| detail_id |  |
| source_tipo |  |
| listing_status |  |
| numero |  |
| anno |  |
| titolo |  |
| pdf_call_title |  |
| numero_posti_html |  |
| data_bando |  |
| data_scadenza |  |
| detail_url |  |
| pdf_url |  |
| pdf_cache_path |  |
| pdf_fetch_status |  |
| first_seen_at |  |
| last_synced_at |  |
| call_title |  |

### calls_curated.csv

One row is one call from the filtered set we use for analysis.
It has the same columns as `calls_raw.csv`, but keeps only these call categories:
`Borsa`, `Incarico di ricerca`, `Incarico Post-Doc`, `Contratto di ricerca`, `Assegno di ricerca`.
Right now it is almost identical to raw, because these are exactly the categories we scrape.

| field | status |
|---|---|
| detail_id |  |
| source_tipo |  |
| listing_status |  |
| numero |  |
| anno |  |
| titolo |  |
| pdf_call_title |  |
| numero_posti_html |  |
| data_bando |  |
| data_scadenza |  |
| detail_url |  |
| pdf_url |  |
| pdf_cache_path |  |
| pdf_fetch_status |  |
| first_seen_at |  |
| last_synced_at |  |
| call_title |  |

### position_rows_raw.csv

One row is one position found inside a PDF call.
It stores extracted values and the text lines used to find them.

| field | status |
|---|---|
| detail_id |  |
| position_row_index |  |
| text_quality |  |
| contract_type |  |
| contract_type_raw |  |
| contract_subtype |  |
| contract_subtype_raw |  |
| duration_months |  |
| duration_raw |  |
| section_structure_department |  |
| institute_cost_total_eur |  |
| institute_cost_yearly_eur |  |
| gross_income_total_eur |  |
| gross_income_yearly_eur |  |
| net_income_total_eur |  |
| net_income_yearly_eur |  |
| net_income_monthly_eur |  |
| contract_type_evidence |  |
| contract_subtype_evidence |  |
| duration_evidence |  |
| section_evidence |  |
| institute_cost_evidence |  |
| gross_income_evidence |  |
| net_income_evidence |  |
| parse_confidence |  |

### position_rows_curated.csv

One row is one PDF position, like `position_rows_raw.csv`.
It also includes key call info, so analysis is easier in one file.

| field | status |
|---|---|
| detail_id |  |
| position_row_index |  |
| source_tipo |  |
| listing_status |  |
| numero |  |
| anno |  |
| numero_posti_html |  |
| data_bando |  |
| data_scadenza |  |
| first_seen_at |  |
| last_synced_at |  |
| pdf_fetch_status |  |
| detail_url |  |
| pdf_url |  |
| pdf_cache_path |  |
| call_title |  |
| text_quality |  |
| contract_type |  |
| contract_type_raw |  |
| contract_subtype |  |
| contract_subtype_raw |  |
| duration_months |  |
| duration_raw |  |
| section_structure_department |  |
| institute_cost_total_eur |  |
| institute_cost_yearly_eur |  |
| gross_income_total_eur |  |
| gross_income_yearly_eur |  |
| net_income_total_eur |  |
| net_income_yearly_eur |  |
| net_income_monthly_eur |  |
| contract_type_evidence |  |
| contract_subtype_evidence |  |
| duration_evidence |  |
| section_evidence |  |
| institute_cost_evidence |  |
| gross_income_evidence |  |
| net_income_evidence |  |
| parse_confidence |  |
