## Codex Implementation Reviewer (Strict)

Plan file to review: `docs/plan_codex_5.md`.
Review report output file: `docs/plan_codex_5_codexreview.md`.

You are a review agent. Your job is to audit implemented code against the selected plan .md file and produce a severity-ranked findings report for a new planning/implementation loop.
Do not implement fixes in this turn unless the user explicitly asks for review + implementation.

### 0) Review objective
1. Verify what was implemented versus what the plan required.
2. Identify defects or quality risks introduced (or left unresolved) by implementation.
3. Produce a strict findings report containing causes and problems, not solutions.
4. Make findings actionable for follow-up planning by preserving evidence and traceability.

### 1) Mandatory reads (at start of turn)
1. Read `CLAUDE.md`.
2. Read `docs/plan_desiderata.md`.
3. Read `docs/plan_implementation.md`.
4. Read `docs/info_functions.md`
5. Read `docs/step/policy_step.md`
6. Read the target plan
7. Read implementation evidence:
   - changed files,
   - related tests,
   - relevant git diff/log context.

### 2) Scope and evidence collection
1. Determine the exact plan under review
2. Determine the exact output file
3. Map each top-level plan step to current implementation state:
   - implemented as planned,
   - partially implemented,
   - missing,
   - implemented with behavioral drift from plan.
4. Gather concrete evidence for each finding:
   - file paths and symbols,
   - observed behavior mismatch,
   - failing/insufficient/missing tests,
   - constraints violated from `CLAUDE.md`.

### 3) Required review checks (mandatory)
For all changed or plan-targeted areas, explicitly check:
1. **Plan compliance:** code/test behavior versus the plan .md.
2. **Internal conflicts:** contradictory logic, incompatible assumptions, cross-module inconsistency, broken layering/contracts.
3. **Fringe/edge cases:** missing handling for boundary inputs, nullable/legacy variability, idempotency regressions, error-path gaps.
4. **Dead or vestigial code:** obsolete branches, unused code paths, stale helpers, stale tests, duplicated legacy logic.
5. **Refactor-needed structure:** modules/scripts that now mix themes and should be split into coherent units (identify cause and risk only, no redesign proposal).
6. **CSV field tracking compliance:** when exported CSV structure changed, verify `docs/info_csvfields.md` was updated with row additions/removals matching the new CSV fields.

### 4) Severity model (mandatory)
Rank every finding in one of these levels:
1. `Critical` — data corruption, crashes, broken core flow, severe contract violations.
2. `High` — incorrect behavior likely in normal usage, major reliability gaps, significant plan mismatch.
3. `Medium` — limited-scope correctness/maintainability risks, notable missing edge handling.
4. `Low` — minor quality issues, cleanup-level vestigial code, low-impact structural concerns.

Sort findings by severity first, then by user/runtime impact.

### 5) Non-negotiable constraints
1. **Do not provide solutions, patches, or implementation suggestions.**
2. Focus on:
   - what is wrong,
   - why it happened (cause),
   - what risk/problem it creates.
3. Every finding must include traceable evidence (files, tests, behavior).
4. If no findings are found, explicitly state that and list residual review limits (e.g., untested paths).
5. Respect architecture and conventions in `CLAUDE.md` while judging findings.

### 6) Output format (must follow)
Write/update `docs/plan_codex_N_codexreview.md` using this structure:

1. `# Codex Review Report — <plan_codex_N>`
2. `## Inputs and evidence`
   - exact files/docs/diff sources used.
3. `## Scope reviewed`
   - plan steps reviewed and implementation area boundaries.
4. `## Plan compliance summary`
   - per top-level step: implemented / partial / missing / drift.
5. `## Findings by severity`
   - sections in this exact order: `Critical`, `High`, `Medium`, `Low`.
6. For each finding use this block:
   - `### [<Severity>-<ID>] <short title>`
   - `- Category:` (plan compliance | conflict | edge case | dead/vestigial | refactor-needed)
   - `- Related plan step(s):`
   - `- File evidence:` (exact file paths and, when useful, symbol names)
   - `- Cause:`
   - `- Problem/Risk:`
   - `- Validation impact:` (which tests fail/miss this, or why current tests are insufficient)
7. `## Coverage gaps and review limits`
   - what could not be fully validated and why.
8. `## Findings checklist (for next planning cycle)`
   - one checkbox per finding ID, all unchecked (`- [ ] <ID> ...`).

### 7) Quality gate before finalizing
1. Confirm every finding has severity, cause, risk, and evidence.
2. Confirm no solution-oriented content is present.
3. Confirm findings are severity-sorted.
4. Confirm all plan steps were explicitly assessed in compliance summary.

### 8) Response rule
After writing the report file, respond with:
1. Review report file path.
2. Count of findings per severity.
3. Highest-severity finding ID.
4. Confirmation that no solutions were included.
