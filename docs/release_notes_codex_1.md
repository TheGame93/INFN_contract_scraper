# Release Notes — Audit #1 Remediation

> **Date:** 2026-03-09  
> **Scope:** `docs/audit_1.md` findings F1–F14

## Audit Closure

| Finding | Status | Notes |
|---|---|---|
| F1 | fixed | Detail PDF URL resolution now handles relative hrefs without leading slash; regression test added. |
| F2 | fixed | Orchestrator now catches `requests.RequestException` for detail fetch failures. |
| F3 | fixed | Downloader now catches `requests.RequestException`; error-path test added. |
| F4 | fixed | Income extraction now prefers currency-anchored amounts and avoids picking duration digits. |
| F5 | fixed | Duration extraction now uses two-pass logic and restricted fallback context; avoids `laurea triennale` false positives. |
| F6 | fixed | `parse_date` is explicitly documented as v2/v3 infrastructure. |
| F7 | fixed | Runtime values now align with enums for tipos/listing status/curated filter. |
| F8 | fixed | Added dedicated orchestrator unit tests for happy path and error handling. |
| F9 | fixed | Added dedicated HTTP client configuration tests. |
| F10 | fixed | Added dedicated metadata extractor tests. |
| F11 | fixed | Added dedicated CLI parser/dispatch/DB lifecycle tests. |
| F12 | deferred (intentional) | `pipeline/export.py` remains simple and already covered by e2e tests. |
| F13 | fixed | `run_sync` now rebuilds curated tables when `dry_run=False`; e2e coverage added. |
| F14 | fixed | URL builder now encodes `tipo` query values explicitly. |

## Changelog Summary

- **Resilience improvements**
  - Hardened HTTP error handling in fetch/download paths.
  - Eliminated known parser mis-extractions in income and duration fields.
  - Synced curated tables automatically after non-dry sync runs.

- **New test coverage**
  - Added dedicated test modules for orchestrator, client, metadata, CLI, and settings enum alignment.
  - Added regression tests for real-world parser failures discovered in cached data.
  - Expanded e2e sync checks to validate curated table freshness.

- **Behavioral changes**
  - `build_urls()` now returns URL-encoded `tipo` query values.
  - `run_sync()` now refreshes curated tables at the end of successful non-dry runs.
  - Duration parsing now prioritizes labeled lines and guards bare-word fallback.

- **Deferred item**
  - `F12` intentionally deferred: no standalone unit test for `pipeline/export.py` until logic complexity increases.
