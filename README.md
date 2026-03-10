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
python3 -m infn_jobs --help
python3 -m infn_jobs sync                                  # default source=local: parse/store using calls_raw + local PDF cache
python3 -m infn_jobs sync --source remote                  # bootstrap or full remote sync: fetch + download + parse + DB writes
python3 -m infn_jobs sync --source remote --dry-run        # fetch + parse only, no DB writes
python3 -m infn_jobs sync --source remote --force-refetch  # remote sync and re-download PDFs even if cached
python3 -m infn_jobs sync --source remote --limit-per-tipo 20      # debug partial fetch: first 20 calls per tipo
python3 -m infn_jobs sync --source remote --download-only           # fetch calls + download/cache PDFs only (no parse/store)
python3 -m infn_jobs sync --source remote --download-only --limit-per-tipo 20  # debug cache warm-up
python3 -m infn_jobs sync --source auto                    # local-first; falls back to remote when calls_raw is empty
python3 -m infn_jobs export-csv                            # rebuild curated data and write the 4 CSV files
```

If `calls_raw` is empty and you run default `source=local`, run bootstrap first: `python3 -m infn_jobs sync --source remote` (CLI guidance: "Run sync with --source remote first.").

`--limit-per-tipo` applies to remote discovery flows. `--download-only` and `--force-refetch` are invalid with `--source local`.

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
