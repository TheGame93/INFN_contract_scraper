# Parsing Plan

This document tracks parsing progress field-by-field for each exported CSV.

## calls_raw.csv

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

## calls_curated.csv

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

## position_rows_raw.csv

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

## position_rows_curated.csv

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
