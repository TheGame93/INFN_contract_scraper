# Step Planning — Policy

> **Location:** `docs/step/policy_step.md`
> **See also:** [Step List](planning_step.md)

This file defines the rules for creating, executing, and reviewing implementation steps.
It applies to all coding sessions, including sessions started by a new Claude instance.

---

## Purpose of the Step System

Steps are the bridge between design docs and actual code.
They let any Claude session pick up exactly where the previous one left off,
without re-reading the full codebase or re-deriving the architecture.

---

## File Layout

```
docs/step/
├── policy_step.md          ← this file: rules
├── planning_step.md        ← master tracker: all steps + status
├── implement_step1.md      ← detail for Step 1 (substeps + sub-substeps)
├── implement_step2.md
└── ...
```

`planning_step.md` is always short and scannable.
`implement_stepN.md` files are as detailed as needed.

---

## Level Definitions

| Level | Example | Contains |
|---|---|---|
| **Step** (1) | `Step 4 — Fetch Layer` | Broad goal; one architectural layer or major feature |
| **Substep** (1.x) | `4.2 Listing scraper` | One cohesive feature or module within the step |
| **Sub-substep** (1.x.x) | `4.2.1 Create url_builder.py` | One concrete file/function/test to write |

A sub-substep is the smallest unit of work: one file created or one function added.

---

## Status Convention

Used in `planning_step.md` and in each `implement_stepN.md`:

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress (current session is working on it) |
| `[x]` | Done and verified |

Mark `[~]` at the start of a session, `[x]` immediately when verified — not at the end of the session.

---

## `planning_step.md` Rules

- Always has a `## Currently Active` section at the very top.
- This section names the exact sub-substep being worked on (e.g., `4.2.1`).
- A new Claude session MUST read this section first before doing anything else.
- Each step entry is one line: status + step number + one-line goal.
- Does NOT contain implementation detail — only the summary and a link to `implement_stepN.md`.

---

## `implement_stepN.md` Template

Each file covers exactly one top-level step. Copy this template exactly:

```markdown
# Step N — [Goal]

> **Location:** `docs/step/implement_stepN.md`
> **Prerequisites:** Step X complete, Step Y complete
> **Produces:**
> - `src/infn_jobs/path/to/file.py`
> - `tests/path/to/test_file.py`
> - (list every file this step creates or significantly edits)

---

## N.1 [Substep name]

### N.1.1 [Sub-substep title]
- **File:** `src/infn_jobs/path/to/file.py`
- **Action:** Create | Edit
- **Write:** `function_name(param: type) -> return_type`
- **Test:** `pytest tests/path/test_file.py::test_name -v`
- **Notes:** edge cases, constraints, era-aware flags, nullable rules, etc.

[ ] done

### N.1.2 [Sub-substep title]
...

**Substep N.1 done when:** all sub-substeps above are `[x]` and
`pytest tests/<relevant_dir>/ -v` passes with no failures.

---

## N.2 [Substep name]
...

---

## Verification

```bash
pytest tests/ -v
ruff check src/
```

Expected: all tests green, ruff exits 0.
[Add any step-specific manual checks here — e.g., run the CLI and check a specific output.]
```

---

## How to Start a New Claude Session

1. Read `CLAUDE.md` (loaded automatically).
2. Read `docs/step/planning_step.md` — check `## Currently Active`.
3. Read the relevant `docs/step/implement_stepN.md` for the active step.
4. Continue from the first `[ ]` sub-substep.
5. Do not re-read the full desiderata or implementation plan unless a specific field is unclear.

---

## How to Add a Step for a New Feature

When a new feature needs to be implemented that was not in the original plan:

1. Add a new `Step N` entry to `planning_step.md` with `[ ]` status.
2. Create `docs/step/implement_stepN.md` using the template above.
3. Set prerequisites based on which layers the new feature touches.
4. If the feature adds new source types or fields, also update:
   - `docs/plan_desiderata.md` (new fields, new test cases)
   - `docs/plan_implementation.md` (file tree, schema)
   - `CLAUDE.md` (Key Conventions if behavior changes)

---

## Checklist: After Each Sub-substep (N.x.x)

Do all of these before marking `[x]`:

1. **Tests pass:** run `pytest <Test field from the sub-substep block> -v` — green.
2. **Ruff clean:** run `ruff check src/infn_jobs/<file just written>.py` — zero errors.
3. **`docs/info_functions.md` updated:** add an entry for every new function or class.
4. **Edge cases logged:** if any unexpected behavior was found, add to `docs/known_edge_cases.md`.
5. **Conventions updated:** if a new reusable pattern was established, add a bullet to `CLAUDE.md` Key Conventions.
6. **Mark `[x]`** on this sub-substep in `implement_stepN.md`.
7. **Update `## Currently Active`** in `planning_step.md` to the next `[ ]` item.
8. **Git snippet** at the end of the response:

```bash
git add <all files created or modified>
git commit -m "<type>(<scope>): <what was done> (generated by Claude Code)"
```

**Public repo warning:** never `git add` data files, credentials, or `.claude/settings.local.json`.
Stage specific files by name — never `git add .` or `git add -A`.

Commit types: `feat` (new function/file), `test` (test only), `fix` (bug fix), `docs` (doc update), `refactor`.

---

## Checklist: After Each Substep (N.x)

Do all of these when all sub-substeps of a substep are `[x]`:

1. **Module tests pass:** run `pytest tests/<relevant module dir>/ -v` — all green.
2. **API sanity check:** confirm the public API (function signatures, return types) matches what the next layer expects per `docs/plan_implementation.md`.
3. **`docs/info_functions.md` complete:** verify all functions in this substep have entries.
4. **Mark `[x]`** on this substep in both `implement_stepN.md` and `planning_step.md`.
5. **Git snippet** grouping all sub-substep files:

```bash
git add <all files for this substep>
git commit -m "feat(<scope>): complete substep N.x — <substep name> (generated by Claude Code)"
```

---

## Checklist: After Each Full Step (N)

Do all of these when all substeps are `[x]`:

1. **Full test suite:** run `pytest tests/ -v` — zero failures.
2. **Ruff on full src:** run `ruff check src/` — zero errors.
3. **Step verification:** run the `## Verification` block in `implement_stepN.md` and confirm expected output.
4. **File tree check:** compare actual files created against the `> **Produces:**` list in `implement_stepN.md` and against `docs/plan_implementation.md`. Fix any gaps.
5. **`docs/plan_implementation.md` sync:** if any structural decision changed during implementation (a file added/removed/renamed), update the file tree in `plan_implementation.md`.
6. **`CLAUDE.md` sync:** if any key convention changed or was established, update `## Key Conventions`.
7. **Mark `[x]`** on the step in `planning_step.md` Completion Summary table.
8. **Update `## Currently Active`** to the first sub-substep of the next step.
9. **Git snippet** for the full step:

```bash
git add <all files produced by this step>
git commit -m "feat(<layer>): complete Step N — <step name> (generated by Claude Code)"
```

---

## Partial Session Handling

If a Claude session ends before a sub-substep is verified:

1. Mark the sub-substep `[~]` in `implement_stepN.md` (not `[x]`).
2. Update `## Currently Active` in `planning_step.md` to point to that `[~]` item.
3. Leave a one-line note in the implement file below the `[~]` line describing what was done and what remains.

The next session reads `[~]` as "started but not verified — resume here".

---

## Fixture-First Rule

For every sub-substep that involves a parser, scraper, or field extractor:

1. The fixture sub-substep (`add tests/fixtures/...`) **must be marked `[x]`** before writing the parser.
2. The test sub-substep must be written **before** marking the parser sub-substep `[x]`.
3. Order is always: **fixture → parser → test → mark done**.

Do not write a parser and then discover the fixture is missing mid-stream.

---

## What NOT to Do

- Do not skip writing tests for a sub-substep — tests are part of the sub-substep.
- Do not mark `[x]` before the verification command passes.
- Do not add implementation detail to `planning_step.md` — it belongs in `implement_stepN.md`.
- Do not re-derive architecture from scratch — always read `docs/plan_implementation.md` first.
- Do not create a function without adding it to `docs/info_functions.md`.
