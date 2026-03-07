- review overall planning using a top/down approach:
    - "plan_desiderata" is my goal
    - "plan_implementation" is the broad planning - does it satisfy my goal?
    - CLAUDE.md is the AI instruction file - does it address all the key weak spots of "plan_implementation.md"?
    - Are plan_implementation.md and CLAUDE.md coherent?
- Review step planning
    - Review planning_step.md - does it comply with the "_desiderata" "_implementation" and "CLAUDE"?
    - Review policy_step.md - does it comply with the "_desiderata" "_implementation" and "CLAUDE"?
    
- Review implement_stepN
    - (in a new context window) Read files "CLAUDE.md", "policy_step.md" and "planning_step.md". Review the docs/step/implement_stepN.md, from 1 to 5, one by one. We have to check if the plan is coherent.
    - (in a new context window) Read files "CLAUDE.md", "policy_step.md" and "planning_step.md". Review the docs/step/implement_stepN.md, from 6 to 9, one by one. We have to check if the plan is coherent.

- If the scraping fail is ome part, how is it possible to add manually the missing info? The User can always download and read the PDF if the scraper fails.

- After completing this scraping, i'll implement a new one, in this same git repo, in which I want to scrape a list of websites (1 or more) searching for the winning position for each grant. These websites will require likely an account+pwd+2FA access and can be nested: we will serach for the "delibere" by the "INFN Giunta" or "INFN Direttivo" regarding the winning position.
    - is the code we planned compatible with this upgrade? Can we update the planning to be as much compatible as possible with this next step in mind?