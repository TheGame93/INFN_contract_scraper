<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A5EA8,100:1F2937&height=220&section=header&text=INFN%20Jobs%20Scraper&fontSize=42&fontColor=ffffff&animation=fadeIn&desc=Fetch%20-%3E%20Parse%20PDFs%20-%3E%20Export%20Analytics-Ready%20CSV&descSize=15&descAlignY=63" alt="INFN Jobs Scraper banner" />
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  </a>
  <a href="https://jobs.dsi.infn.it/">
    <img src="https://img.shields.io/badge/Target-jobs.dsi.infn.it-0A5EA8?style=for-the-badge&logo=firefox-browser&logoColor=white" alt="Target jobs.dsi.infn.it" />
  </a>
  <a href="https://github.com/TheGame93/INFN_contract_scraper/tree/main/data">
    <img src="https://img.shields.io/badge/Output-SQLite%20%2B%204%20CSV-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="Output SQLite and CSV" />
  </a>
</p>

<p align="center">
  <a href="https://github.com/TheGame93/INFN_contract_scraper/stargazers">
    <img src="https://img.shields.io/github/stars/TheGame93/INFN_contract_scraper?style=flat-square" alt="GitHub stars" />
  </a>
  <a href="https://github.com/TheGame93/INFN_contract_scraper/commits/main">
    <img src="https://img.shields.io/github/last-commit/TheGame93/INFN_contract_scraper?style=flat-square" alt="Last commit" />
  </a>
  <a href="https://github.com/TheGame93/INFN_contract_scraper/issues">
    <img src="https://img.shields.io/github/issues/TheGame93/INFN_contract_scraper?style=flat-square" alt="Open issues" />
  </a>
</p>

Scraper for [jobs.dsi.infn.it](https://jobs.dsi.infn.it/).

Goal: build an analytics-ready dataset of INFN opportunities (borse, assegni di ricerca, incarichi di ricerca, incarichi post-doc, contratti di ricerca), extracting key fields from listings and PDF calls (title, structure, type/subtype, duration, deadlines, positions, and economic data when available).

## Table of Contents

- [Overview](#overview)
- [What You Get](#what-you-get)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Sync Option Matrix](#sync-option-matrix)
- [Output Artifacts](#output-artifacts)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

## Overview

This project scrapes INFN job calls from listings and detail pages, downloads the related PDFs, parses position-level information, and writes both raw and curated datasets for analysis.

## What You Get

You get four CSV files because the data is split in two ways:

1. By granularity:
   - `calls_*`: one row per call/announcement.
   - `position_rows_*`: one row per position found inside call PDFs.
2. By cleaning level:
   - `*_raw`: close to the original extraction.
   - `*_curated`: normalized and easier to analyze.

That gives `2 x 2 = 4` exports:

| File | Why you would use it |
| --- | --- |
| `calls_raw.csv` | Keep original call metadata for auditing and debugging extraction |
| `calls_curated.csv` | Analyze calls quickly with cleaner and normalized fields |
| `position_rows_raw.csv` | Inspect raw position-level extraction from PDF text |
| `position_rows_curated.csv` | Do analytics on positions with cleaner values |

## Quick Start

### 1. Clone

```bash
gh repo clone TheGame93/INFN_contract_scraper .
# or
git clone git@github.com:TheGame93/INFN_contract_scraper.git
```

### 2. Create environment and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r pythonrequirements.txt
```

### 3. Smoke run (small remote batch)

```bash
python3 -m infn_jobs --help
python3 -m infn_jobs sync --source remote --limit-per-tipo 10
python3 -m infn_jobs export-csv
```

### 4. Full remote bootstrap

With the current number of contracts and with a standard internet connection, the full download takes about 4 hours.

```bash
python3 -m infn_jobs sync --source remote
python3 -m infn_jobs export-csv
```

### 5. Routine updates

```bash
python3 -m infn_jobs sync --source auto
python3 -m infn_jobs export-csv
```

## Commands

| Command | Purpose |
| --- | --- |
| `python3 -m infn_jobs sync` | Parse local DB/cache entries (default `source=local`) |
| `python3 -m infn_jobs sync --source remote` | Re-discover from network and materialize cache |
| `python3 -m infn_jobs sync --source auto` | Use local first; fallback to remote if DB is empty |
| `python3 -m infn_jobs export-csv` | Rebuild curated tables and export the 4 CSV files |

## Sync Option Matrix

| Flag | Default | Notes |
| --- | --- | --- |
| `--source {local,remote,auto}` | `local` | Discovery + cache strategy |
| `--dry-run` | `False` | Parse only; skip DB writes |
| `--force-refetch` | `False` | Re-download PDFs (remote/auto flows) |
| `--download-only` | `False` | Build cache only; skip parse and DB writes (`--dry-run` has no extra effect) |
| `--limit-per-tipo N` | `None` | Positive integer, used in remote discovery flows |

<details>
<summary><strong>Source behavior details</strong></summary>

### `source=local`

```bash
python3 -m infn_jobs sync
python3 -m infn_jobs sync --dry-run
```

- Uses DB/cache only.
- If DB is empty, run one remote bootstrap first.

### `source=remote`

```bash
python3 -m infn_jobs sync --source remote
python3 -m infn_jobs sync --source remote --dry-run
python3 -m infn_jobs sync --source remote --force-refetch
python3 -m infn_jobs sync --source remote --limit-per-tipo 20
python3 -m infn_jobs sync --source remote --download-only
```

- Always re-discovers calls from network.
- Materializes PDF cache through downloader.

### `source=auto`

```bash
python3 -m infn_jobs sync --source auto
python3 -m infn_jobs sync --source auto --force-refetch
python3 -m infn_jobs sync --source auto --limit-per-tipo 20
```

- Uses local DB first.
- Falls back to remote discovery only when local DB is empty.
- Downloads missing/invalid cache files when URLs are available.

</details>

<details>
<summary><strong>Invalid combinations (fail fast)</strong></summary>

```bash
python3 -m infn_jobs sync --download-only
python3 -m infn_jobs sync --force-refetch
python3 -m infn_jobs sync --source local --download-only
python3 -m infn_jobs sync --source local --force-refetch
python3 -m infn_jobs sync --limit-per-tipo 0
```

</details>

## Output Artifacts

- SQLite DB: `data/infn_jobs.db`
- CSV exports in `data/exports/`:
  - `calls_raw.csv`
  - `calls_curated.csv`
  - `position_rows_raw.csv`
  - `position_rows_curated.csv`
- PDF cache: `data/pdf_cache/`

## Roadmap

- [x] Full download from [jobs.dsi.infn.it](https://jobs.dsi.infn.it/)
- [ ] Fill DB with high-quality parsed entries
- [ ] Analytics notebooks/dashboards on curated outputs

## Disclaimer

This codebase has been written with **heavy** AI assistance.
