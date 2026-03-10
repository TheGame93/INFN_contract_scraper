- review overall planning using a top/down approach:
    - "plan_desiderata" is my goal
    - "plan_implementation" is the broad planning - does it satisfy my goal?
    - CLAUDE.md is the AI instruction file - does it address all the key weak spots of "plan_implementation.md"?
    - Are plan_implementation.md and CLAUDE.md coherent? If not, fix them.
- Review step planning
    - Review planning_step.md - does it comply with the "_desiderata" "_implementation" and "CLAUDE"? If not, fix it.
    - Review policy_step.md - does it comply with the "_desiderata" "_implementation" and "CLAUDE"? If not, fix it.
- Review implement_stepN
    - Read files "CLAUDE.md", "policy_step.md" and "planning_step.md". Review the docs/step/implement_stepN.md, from 1 to 9, one by one. We have to check if the plan is coherent. If not, fix it.

## Review

If something important change in the code, review the command /review-full-code

## Question


## Feature

- Let's talk about the database columns. Which are them now? Is the program flexible about the creation of new fields? Is there a dedicated interface for managing fields?
    - Current state: columns are duplicated across at least 4 places: schema DDL, dataclasses, upsert SQL, export/view/tests. Best pragmatic setup is a single source of truth per table plus generated SQL.
        - How the "logic" works? If i set a column where should the rule for filling the column is?
    - Can we make a single entry point to change? Or is it necessary that they are spread into more files? I want that changing the fields will be a "coded" thing. It's not something that will be made while the program is running. The code has to change.
        - How many files do I need to keep this clean? I want to avoid repetitions but I'm ok with having multiple files in nested folders (always check CLAUDE.md for the general rules)


## Codex

1. Plan with `docs/codex_planning.md`, creating `plan_codex_N.md`
2. Implement it with `docs/codex_instructions.md`
3. Review it with `docs/codex_reviewing.md`, creating `docs/plan_codex_N_codexreview.md`
4. Plan again with `docs/codex_planning.md` with the "### 0) The things I want to do" command
    > Read the things to fix from `docs/plan_codex_3_codexreview.md`

## Future

- After completing this scraping, i'll implement a new one, in this same git repo, in which I want to scrape a list of websites (1 or more) searching for the winning position for each grant. These websites will require likely an account+pwd+2FA access and can be nested: we will serach for the "delibere" by the "INFN" "Giunta" or "Direttivo" regarding the winning position, usually but not always from PDF files.
    - the code have to be planned compatible with this future upgrade. The refactoring of the utilities should be as atomic as possible, in order to use them to both scraping.
Modifie the current .md files in order to comply.

- Up to now the plan doesn't include any analytics. Add to the plan the fact that a future implementation will be analytics of the output. The first analytics will be for the position scraping. The second analytics will be for the winning scrapings (w.r.t. the position scraping).
Modifie the current .md files in order to comply.