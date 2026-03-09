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

Update README.md: be very short. I want
- info about how to run the code (all the options)
- which will be the output
- a final disclaimer that has been written totally with AI

## Review

I just finished vibe coding the program (with Sonnet 4.6), following info in docs/ folder and CLAUDE.md. This vibe coding spanned multiple sessions. This can be source of problems: dead code, details that have been missed due to compacting the context window, and due to the limited scope of each implementation step.
Write me a prompt for
- checking that everything planned has been implemented
- there is the right interplay between the parts
- searching for logical bugs or missed fringe case
Give me only the prompt. I want to review it before launching it.

## Question


## Future

- After completing this scraping, i'll implement a new one, in this same git repo, in which I want to scrape a list of websites (1 or more) searching for the winning position for each grant. These websites will require likely an account+pwd+2FA access and can be nested: we will serach for the "delibere" by the "INFN" "Giunta" or "Direttivo" regarding the winning position, usually but not always from PDF files.
    - the code have to be planned compatible with this future upgrade. The refactoring of the utilities should be as atomic as possible, in order to use them to both scraping.
Modifie the current .md files in order to comply.

- Up to now the plan doesn't include any analytics. Add to the plan the fact that a future implementation will be analytics of the output. The first analytics will be for the position scraping. The second analytics will be for the winning scrapings (w.r.t. the position scraping).
Modifie the current .md files in order to comply.