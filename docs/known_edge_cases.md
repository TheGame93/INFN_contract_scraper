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

<!-- Add entries as they are discovered during implementation and QA. -->
