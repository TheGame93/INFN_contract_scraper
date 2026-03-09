# Known Edge Cases

> **Location:** `docs/known_edge_cases.md`
> **See also:** [Desiderata](plan_desiderata.md) · [Implementation Plan](plan_implementation.md)

This file records specific `detail_id` values or patterns that caused parser failures or unexpected behavior.
It is the regression specification: every entry here should eventually have a corresponding test fixture.

---

## How to Add an Entry

```
### detail_id=XXXX — [short description]
- **Discovered:** YYYY-MM-DD
- **Layer:** fetch | extract | store
- **Symptom:** what went wrong or what was unexpected
- **Root cause:** if known
- **Status:** open | fixed | test added
- **Fixture:** `tests/fixtures/...` (if created)
```

---

## Entries

### listing parser — relative href missing leading slash
- **Discovered:** 2026-03-09
- **Layer:** fetch
- **Symptom:** Live sync crashed with `ConnectionError` — hostname resolved as `jobs.dsi.infn.itdettagli_job.php` (path smashed onto host).
- **Root cause:** The site produces listing hrefs without a leading slash: `dettagli_job.php?id=N`. `_resolve_url` in `fetch/listing/parser.py` did `_ORIGIN + href` (missing `/` separator). PDF hrefs in the detail page start with `/` and were unaffected.
- **Status:** fixed
- **Fix:** `_resolve_url` now adds `/` when the href does not start with `/` or `http`. A regression test `test_parse_rows_detail_url_correct_format` was added to `tests/fetch/test_listing_parser.py`.

### income parser — duration number captured as gross amount
- **Discovered:** 2026-03-09
- **Layer:** extract
- **Symptom:** Gross income fields were parsed as month counts (e.g., `6.0`) when a line contained both `durata di 6 mesi` and a later EUR amount.
- **Root cause:** `extract_income` used a first-match numeric regex; in lines like `"...durata di 6 mesi... € 8.677,50"` it matched `6` before the real amount.
- **Status:** fixed
- **Fix:** Amount extraction now starts after the matched label and prefers currency-anchored amounts (`€` or `euro`) before fallback numeric patterns. Regression tests were added in `tests/extract/fields/test_income.py`.
- **Examples:** `detail_id=4140`, `detail_id=4062`.

### duration parser — fallback matched academic text (`laurea triennale`)
- **Discovered:** 2026-03-09
- **Layer:** extract
- **Symptom:** `duration_months=36` was assigned from unrelated lines mentioning `laurea triennale`.
- **Root cause:** Word-based fallback (`triennale|biennale|annuale`) ran on every line and accepted non-duration contexts.
- **Status:** fixed
- **Fix:** Duration extraction now uses a two-pass strategy (labeled first) and restricts bare-word fallback to duration-like context lines; `un mese` was also added for labeled lines. Regression tests were added in `tests/extract/fields/test_duration.py`.
- **Examples:** `detail_id=4506`, `detail_id=4317`.
