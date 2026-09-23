What problem does it solve, and for whom? Name a real, specific user. "Everyone" is not a user.
Problem: Low-income young adults experience social exclusion because social activities are financially out of reach, while available financial support (discounts, free programs) goes unclaimed due to a lack of awareness (SDG 10, Target 10.2).
Target User: A young adult aged 18–27 living on a low income in the Den Haag region who wants to socialize with friends but struggles to find affordable activities or navigate available local support programs.
For example: Maya, a 21-year-old student living in Den Haag on a tight monthly income who turns down outings with friends because she cannot afford them and does not know which local youth discounts she qualifies for.
	Research: 
CBS — Youth Poverty Statistics:
National level: CBS data shows that 3.1% to 3.6% of youth live in households under the poverty threshold.
Den Haag level: Urban centers face higher rates, with over 12% of children and young people growing up in low-income families.
Source: CBS — Armoede en risico op armoede
Nibud — Financial Stress Among Youth:
Nibud research reveals that 1 in 5 young adults aged 18–26 face severe financial stress or payment issues.
Impact: Leisure activities, culture, and outings are the first expenses cut when budgets are tight, driving social isolation.
Source: Nibud — Rapport Geldstress bij jongeren
SCP — Social Exclusion & Non-Participation:
Participation Gap: SCP identifies financial strain as the primary cause of social exclusion. Over 40% of low-income youth miss out on regular social activities due to cost.
Unclaimed Support: Many eligible young adults miss available financial support (like municipal discount passes) simply due to a lack of awareness.
Source: SCP — Armoede en Sociale Uitsluiting

What did you build? Two or three sentences. What can a user actually do with it?
What we built: A Streamlit Python app using the Claude API and live web search to connect low-income youth in Den Haag with verified local discounts and activities, strictly dropping any price or eligibility claim that lacks a source link.
What a user can do:
Enter their total budget, personal interests, and group size.
See financial support options they likely qualify for (e.g., Ooievaarspas, CJP) with direct links to verify.
Get a tailored list of current local events/activities complete with date, price per person, total budget breakdown, and source links.
Generate and copy a ready-to-send group invite text for their friends.
Link to the live thing (if any): Deployed URL, workflow export, video demo - whatever proves it works.
GitHub Repository: github.com/nemoyrolls/meedoen (renaming to outtogether-ai)
Demo Video: [Link to 2-minute demo recording]
Deployed App: [Link to live Streamlit app URL]
Who did what? Be honest about the split of work between you and your partner.
Majed: Handled all technical development, including the Python codebase, Streamlit UI, Claude API integration, budget calculation logic, and handling edge cases.
Ana: Led research and documentation, including docs/research.md (youth poverty data from CBS, Nibud, SCP), the project README, the ethical reflection, slides, and the 2-minute demo video.
