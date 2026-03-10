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
#old
python3 -m infn_jobs --help               # show all commands and flags
python3 -m infn_jobs sync                 # full sync: fetch + parse + write to DB
python3 -m infn_jobs sync --dry-run       # fetch + parse only, no DB writes
python3 -m infn_jobs sync --force-refetch # full sync and re-download PDFs even if cached
python3 -m infn_jobs export-csv           # rebuild curated data and write the 4 CSV files
```

```bash
#new
python3 -m infn_jobs --help
python3 -m infn_jobs sync                                  # default local mode: parse/store from local cache + existing DB metadata
python3 -m infn_jobs sync --source remote                  # full remote sync: fetch + download + parse + write to DB
python3 -m infn_jobs sync --source remote --dry-run        # fetch + parse only, no DB writes
python3 -m infn_jobs sync --source remote --force-refetch  # full remote sync and re-download PDFs even if cached
python3 -m infn_jobs sync --source remote --limit-per-tipo 20   # debug partial fetch: first 20 calls per tipo
python3 -m infn_jobs sync --source remote --download-only        # fetch calls + download/cache PDFs only (no parse/store)
python3 -m infn_jobs sync --source remote --download-only --limit-per-tipo 20  # debug cache warm-up
python3 -m infn_jobs sync --source local --dry-run         # parse local cached PDFs only, no DB writes
python3 -m infn_jobs sync --source auto                    # hybrid mode (local-first behavior, remote when needed)
python3 -m infn_jobs export-csv                            # rebuild curated data and write the 4 CSV files
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

This code has been written totally with AI.
