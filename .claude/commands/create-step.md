You are generating the next `implement_stepN.md` file for this project.
Only create the implement file — do not edit any other doc.

---

## Phase 1 — Read all reference docs

Read ALL of these before generating anything:
- `docs/step/planning_step.md` — all steps and substeps
- `docs/step/policy_step.md` — implement file template and rules (including the `[ ] done` per sub-substep requirement)
- `docs/plan_implementation.md` — source file tree, function signatures, DB schema, test file tree
- `docs/plan_desiderata.md` — test plan, field rules, era variants, failure handling
- `CLAUDE.md` — key conventions (nullable rules, encoding, rate limit, fixture-first scope, etc.)
- `docs/known_edge_cases.md` — edge cases to pre-populate Notes fields

Then use Glob to list existing files in `docs/step/implement_step*.md`.
If any exist, read the highest-numbered one to calibrate: note depth, sub-substep naming style,
and level of detail — then match that register.

---

## Phase 2 — Select target step

Find the lowest N where `docs/step/implement_stepN.md` does not yet exist.
State: "Generating `implement_stepN.md` — Step N: [step name from planning_step.md]"

---

## Phase 3 — Generate

Write `docs/step/implement_stepN.md` following the policy_step.md template exactly.

### Sub-substep expansion

Each substep from `planning_step.md` expands into one or more atomic sub-substeps.
One sub-substep = one file created OR one function added — never mix two files in one sub-substep.

**Fixture-first rule** — applies only to HTML and PDF text parsers (not to normalization
functions whose test data is inline):
For any substep that produces a parser reading external HTML or PDF text, order sub-substeps as:
  1. Add fixture file (`tests/fixtures/html/` or `tests/fixtures/pdf_text/`)
  2. Write the parser/extractor function
  3. Write the test function

### Per sub-substep fields

Adapt these fields based on the sub-substep type:

**Implementation sub-substep** (creating a function or class):
- **File:** exact path from `plan_implementation.md` source file tree
- **Action:** `Create` or `Edit`
- **Write:** exact function signature from `plan_implementation.md` and `CLAUDE.md`;
  use `# infer from context` only for undocumented private helpers
- **Test:** `pytest tests/path/test_file.py::test_specific_function_name -v`
  — use specific test function names from the desiderata test plan where known
- **Notes:** include whichever apply — nullable rules, era-aware flags,
  encoding (`response.content` not `response.text`), rate-limit sleep,
  field variability across eras, known edge cases from `known_edge_cases.md`

**Fixture sub-substep** (adding a test fixture file):
- **File:** exact path under `tests/fixtures/`
- **Action:** `Create`
- **Write:** `(fixture file — no function; content described in Notes)`
- **Test:** `(tested by the implementation sub-substep that follows)`
- **Notes:** describe the scenario the fixture represents (e.g. "missing Numero posti, no PDF link")
  and any specific HTML/text patterns that must be present

**Test sub-substep** (adding a test file or test functions):
- **File:** exact path from `plan_implementation.md` test file tree
- **Action:** `Create` or `Edit`
- **Write:** list each test function: `test_name_1`, `test_name_2`, ...
- **Test:** `pytest tests/path/test_file.py -v`
- **Notes:** reference which fixture files are used; note any parametrize patterns needed

**No-automation sub-substep** (manual verification or scaffolding with no testable output):
- **Test:** `(manual verification — [describe what to check])`

### Required closing elements per sub-substep

Every sub-substep block must end with:
```
[ ] done
```

### Substep footers

End every substep N.x with:
```
**Substep N.x done when:** all sub-substeps above are `[x]` and
`pytest tests/<relevant_dir>/ -v` passes with no failures.
```

### File header

```
# Step N — [Goal]

> **Location:** `docs/step/implement_stepN.md`
> **Prerequisites:** Step X complete, Step Y complete
> **Produces:**
> - `src/infn_jobs/path/to/file.py`
> - `tests/path/to/test_file.py`
> - (every file this step creates or significantly edits)
```

Derive **Prerequisites** from the layer dependency table in `plan_implementation.md`
and the step order in `planning_step.md`.

Derive **Produces** from the `plan_implementation.md` source and test file trees.

### Verification section

End the file with:
```markdown
---

## Verification

```bash
pytest tests/ -v
ruff check src/
```

Expected: all tests green, ruff exits 0.
[Add any step-specific manual checks — e.g. run the CLI and verify a specific output.]
```

---

## Phase 4 — Coherence review

After writing the file, run all checks below and fix any issue before finishing.

1. **Coverage:** every substep listed in `planning_step.md § Step N` appears in the implement file;
   none skipped
2. **Tests present:** every implementation sub-substep has either a test sub-substep or references
   an existing test file
3. **Fixture-first:** every HTML/PDF parser sub-substep is preceded by a fixture sub-substep
   in the same substep block (normalization and scaffolding sub-substeps are exempt)
4. **Produces — completeness:** every file listed for step N in `plan_implementation.md`
   (source tree + test tree) appears in `> **Produces:**`
5. **Produces — no phantoms:** every file in `> **Produces:**` exists in `plan_implementation.md`;
   no files invented that aren't in the plan
6. **Prerequisites — correctness:** verify that the types and imports step N depends on
   are produced by the stated prerequisite steps
7. **`[ ] done` present:** every sub-substep block ends with `[ ] done`
8. **No side effects:** `planning_step.md`, `CLAUDE.md`, `plan_implementation.md`,
   and all other docs are unchanged — only the new implement file was written

Report: "Coherence review passed — N sub-substeps across M substeps." or list each issue
found and state how it was fixed, then re-confirm the file is correct.
