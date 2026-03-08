Read `docs/step/planning_step.md`. Find the `## Currently Active` section.

Look for the first `[~]` sub-substep (in-progress from a previous session).
If none, find the first `[ ]` sub-substep (not started).

Then read the relevant `docs/step/implement_stepN.md` file for that step.
If the sub-substep is `[~]`, also read any notes left below the marker about what was done and what remains.

Read `docs/info_functions.md` if it exists — use it for a quick API overview before diving into source files.

Read the relevant sections of `docs/plan_implementation.md` for the active layer (file tree, function signatures, DB schema if applicable).

Mark the current sub-substep as `[~]` in the implement file to signal it is in progress.

Report back:
1. Which sub-substep we are on (e.g. `2.1.1`) and whether it is a fresh start or a resume
2. Which file to create or edit
3. Which function or class to write, with its exact signature
4. Any constraints or notes from the implement file
5. Dependencies from previous steps that this sub-substep relies on
6. Shared utility constraint applies: yes/no (yes if the file is in `extract/pdf/`, `extract/parse/normalize/`, or `fetch/client.py` — these must not import v1-specific logic, per CLAUDE.md)

Do not write any code yet — just confirm the plan. Wait for user approval before proceeding.
