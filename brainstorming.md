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

- We need more options for the code:
    - allow for a partial fetch option: only the first 20 items of each contract type. Is it useful for debug
    - allow for the download of all the PDF: store them locally so if the user wants to analyze them in a different way it doesn't need to fetch them again (since is a slow process).
    - The user will since choose if creating the db from fetch or from local source
    - Of course the local save should be incremental: an already downloaded pdf will not be downloaded again.

- Let's talk about the database columns. Which are them now? Is the program flexible about the creation of new fields? Is there a dedicated interface for managing fields?

## Codex

Plan with `docs/codex_planning.md`, creating `plan_codex_N.md`.
Implement it with `docs/codex_instructions.md`

## Future

- After completing this scraping, i'll implement a new one, in this same git repo, in which I want to scrape a list of websites (1 or more) searching for the winning position for each grant. These websites will require likely an account+pwd+2FA access and can be nested: we will serach for the "delibere" by the "INFN" "Giunta" or "Direttivo" regarding the winning position, usually but not always from PDF files.
    - the code have to be planned compatible with this future upgrade. The refactoring of the utilities should be as atomic as possible, in order to use them to both scraping.
Modifie the current .md files in order to comply.

- Up to now the plan doesn't include any analytics. Add to the plan the fact that a future implementation will be analytics of the output. The first analytics will be for the position scraping. The second analytics will be for the winning scrapings (w.r.t. the position scraping).
Modifie the current .md files in order to comply.