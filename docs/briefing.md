The assignment: Hackathon 3, AI for Good. Build a Python tool that makes live Claude API calls and reduces a specific inequality under SDG 10. Due before Friday's session of week 4.

The problem we're solving: young adults (18–27) on a low income in the Den Haag region drop out of social life because they can't afford it. At the same time, discounts and free programs meant for exactly this go unclaimed because people don't know they exist. SDG 10, target 10.2: social inclusion regardless of economic status.

What the tool does:

The user enters a budget, interests, and group size.
It shows support they likely qualify for (Ooievaarspas, CJP, youth programs) with official links.
Claude with web search finds cheap or free activities, each with price, date and source link.
Python fits as much as possible into the budget and calculates cost per person.
It generates a ready-to-send invite message for friends.

Built with: Python, the Claude API, and Streamlit for the web app.

The hard rule: the AI never states a price or eligibility from memory. Everything comes with a source link and a date; anything unsourced gets dropped. Eligibility is always "likely, check here," never "you qualify." Wrong info to people who can't verify it is our biggest risk.

Repo: github.com/nemoyrolls/meedoen (name changing to outtogether-ai).

Split — Majed: all the code (API calls, budget logic, UI, edge cases).
Split — Ana:

docs/research.md: sourced numbers on youth poverty and social exclusion in NL (CBS, Nibud, SCP), with links. The teachers want real numbers with solid sources.
docs/test_cases.md: 10 test cases (normal use, €0 budget, nonsense input, English input) and what went wrong.
README and the ethical reflection.
The demo recording, about 2 minutes.

How to work: no installs needed. On github.com, open a file, click the pencil icon, edit, and click Commit changes.
