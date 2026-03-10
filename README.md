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
python3 -m infn_jobs export-csv                            # rebuild curated data and write the 4 CSV files
```

### Sync Option Matrix (Pedantic)

The `sync` command has these flags:
- `--source {local,remote,auto}` (default: `local`)
- `--dry-run`
- `--force-refetch`
- `--download-only`
- `--limit-per-tipo N` (must be a positive integer)

First run bootstrap? : run the code with `--source remote`

#### `source=local` (DB/cache-only discovery)

Not specifying source is like running `--source local`

```bash
python3 -m infn_jobs sync
python3 -m infn_jobs sync --dry-run
```

- In `source=local`, `--limit-per-tipo` is accepted but has no effect (no remote listing fetch happens).

#### `source=remote` (network listing/detail discovery)

```bash
# full pipeline variants
python3 -m infn_jobs sync --source remote
python3 -m infn_jobs sync --source remote --dry-run
python3 -m infn_jobs sync --source remote --force-refetch
python3 -m infn_jobs sync --source remote --limit-per-tipo 20
```

```bash
# cache-materialization-only variants
python3 -m infn_jobs sync --source remote --download-only
python3 -m infn_jobs sync --source remote --download-only --force-refetch
python3 -m infn_jobs sync --source remote --download-only --limit-per-tipo 20
```

Option `--download.only` is not compatible with `--dry-run`: it would have the same behavior as equivalent command without `--dry-run`.

#### `source=auto` (local-first, remote fallback)

Same commands as before, with the following caveat:
- In `source=auto`, `--limit-per-tipo` is used only if auto falls back to remote discovery.
- In `source=auto` with non-empty local DB, `--force-refetch` does not re-download already-valid local cache files; it affects cache materialization for missing/invalid files and remote-fallback flows.

#### Invalid combinations (fail fast)

```bash
python3 -m infn_jobs sync --download-only     # invalid because default source is local
python3 -m infn_jobs sync --force-refetch     # invalid because default source is local
python3 -m infn_jobs sync --source local --download-only
python3 -m infn_jobs sync --source local --force-refetch
python3 -m infn_jobs sync --limit-per-tipo 0      # also invalid for negative values
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
