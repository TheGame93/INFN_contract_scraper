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

First set of findings: docs/audit_1.md

## Question


## Future

- After completing this scraping, i'll implement a new one, in this same git repo, in which I want to scrape a list of websites (1 or more) searching for the winning position for each grant. These websites will require likely an account+pwd+2FA access and can be nested: we will serach for the "delibere" by the "INFN" "Giunta" or "Direttivo" regarding the winning position, usually but not always from PDF files.
    - the code have to be planned compatible with this future upgrade. The refactoring of the utilities should be as atomic as possible, in order to use them to both scraping.
Modifie the current .md files in order to comply.

- Up to now the plan doesn't include any analytics. Add to the plan the fact that a future implementation will be analytics of the output. The first analytics will be for the position scraping. The second analytics will be for the winning scrapings (w.r.t. the position scraping).
Modifie the current .md files in order to comply.