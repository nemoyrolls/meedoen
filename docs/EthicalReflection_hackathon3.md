# Ethical Reflection: Risks, Harm, and Mitigations

**TagAlong — Hackathon 3, AI for Good**
Majed Al-Sakkaf & Ana Talg Wolf

## Risks and potential harm

- **Money lost through wrong information.** Our users have little or no financial buffer. A wrong price, or a made-up "free entry", could mean unexpected costs or embarrassment in front of friends. According to [Nibud](https://www.nibud.nl/onderzoeksrapporten/rapport-geldstress-bij-jongeren-2022/), 1 in 5 young adults face severe financial stress, and [CBS](https://www.cbs.nl/nl-nl/publicatie/2023/51/armoede-sociale-uitsluiting-2023) figures show over 12% of young people in Den Haag grow up in low-income households.
- **Language gap.** Many municipal and event sites are in Dutch only, so non-Dutch speakers may get weaker results. That risks worse service for migrant and international youth.
- **Pictures from other websites.** Result cards load each event page's own image, so those sites can see that the picture was requested.
- **Cost abuse through a public link.** Anyone with the live link can run searches that spend our API credits.

## How we limit it

- **No source, no listing.** The Python code drops any activity that has no source link, and any item with a date in the past or outside the chosen dates. Every price and date is copied from the page, never estimated. Ongoing deals with no date are kept only when they have a link.
- **No claims from memory.** The AI may not state prices or eligibility rules from its own knowledge; everything comes from the live web search.
- **The official page decides eligibility.** The app never tells users they qualify for a pass. It links to the official page (gemeente, government, school or pass website only), because only that page can say who qualifies.
- **Safe display.** Text from the web is escaped before it is shown, so a web page cannot inject code. The share link in invites is added by the code, so the AI cannot invent or change it.
- **Spending cap.** A monthly spend limit on the API account caps what a misused public link can cost.

## Known limits

A search takes about 15 to 30 seconds, results depend on what the web search finds, some cards have no picture, and saved items disappear when the page is closed.
