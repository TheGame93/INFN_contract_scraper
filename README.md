# INFN Jobs Scraper

Scraper for `https://jobs.dsi.infn.it/`.

Goal: build an analytics-ready dataset of INFN opportunities (borse, assegni di ricerca, incarichi di ricerca, incarichi post-doc, contratti di ricerca), extracting key fields from listings and PDF calls (title, structure, type/subtype, duration, deadlines, positions, and economic data when available).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r pythonrequirements.txt
```

```bash
python3 -m infn_jobs sync
python3 -m infn_jobs sync --dry-run
python3 -m infn_jobs sync --force-refetch
python3 -m infn_jobs export-csv
```

## Output

- SQLite DB: `data/infn_jobs.db`
- CSV files in `data/exports/`:
  - `calls_raw.csv`
  - `calls_curated.csv`
  - `position_rows_raw.csv`
  - `position_rows_curated.csv`
- PDF cache in `data/pdf_cache/`

## Disclaimer

This README has been written totally with AI.
