# TagAlong

**Hackathon 3 — AI for Good**

| | |
|---|---|
| **Pair** | Majed Al-Sakkaf & Ana Talg Wolf |
| **Tool we had to use** | API + Python code |
| **Live app** | [tagalong.streamlit.io](https://tagalong.streamlit.io) |
| **Demo video** | [YouTube link — to be added] |
| **GitHub** | [github.com/nemoyrolls/meedoen](https://github.com/nemoyrolls/meedoen) (to be renamed to `tagalong`) |

## What problem does it solve, and for whom?

- **Problem:** Low-income young adults get shut out of social life because going out costs money they don't have. Discounts, free events and city passes exist, but many people never find them (SDG 10, Target 10.2).
- **Target user:** A young adult aged 18–27 on a low income in the Netherlands who wants to go out with friends but struggles to find things they can afford.
- **Example user:** Maya, 21, a student in Den Haag on a tight monthly budget. She turns down outings with friends because she can't afford them and doesn't know which youth discounts or passes could make them cheaper.

### Research

- **CBS — youth poverty**
  - National: 3.1% to 3.6% of youth live in households below the poverty threshold.
  - Den Haag: urban areas score higher, with over 12% of children and young people growing up in low-income families.
  - Source: [CBS — Armoede en sociale uitsluiting 2023](https://www.cbs.nl/nl-nl/publicatie/2023/51/armoede-sociale-uitsluiting-2023)
- **Nibud — financial stress among youth**
  - 1 in 5 young adults aged 18–26 face severe financial stress or payment problems.
  - Leisure, culture and going out are the first costs cut when money is tight, which drives social isolation.
  - Source: [Nibud — Rapport Geldstress bij jongeren (2022)](https://www.nibud.nl/onderzoeksrapporten/rapport-geldstress-bij-jongeren-2022/)
- **SCP — social exclusion**
  - Financial strain is a main cause of social exclusion, and many eligible young adults miss support such as municipal discount passes simply because they don't know about it.
  - Source: [SCP — Armoede in kaart 2018](https://digitaal.scp.nl/armoedeinkaart2018/assets/pdf/armoede-in-kaart-2018-SCP.pdf)

## Which SDG does it address and why?

**SDG 10 — Reduced Inequalities, Target 10.2:** promote the social, economic and political inclusion of all, irrespective of economic status.

- **Removes cost as a barrier to taking part.** TagAlong finds free and cheap activities within the user's budget, so social life doesn't depend on income.
- **Closes the information gap on support.** City passes and youth cards (Ooievaarspas, U-pas, CJP) exist to reduce inequality but often go unused. TagAlong points users to them, with links to the official pages.

## What did we build?

A Streamlit app in Python that uses the Claude API with live web search to find cheap and free activities in any Dutch city. Claude finds and copies information from the web; plain Python decides what is shown, so the AI never has the last word on a price, date or eligibility.

What a user can do:

- **Search:** pick categories (parties, festivals, deals, cheap trips, live music, culture, sport and more), a city, a max price per person, group size, and a time window or exact dates.
- **See results:** picture cards sorted cheapest first, with date, price, deal, city-pass price, who can join and the group total. Anything over budget, outside the dates or without a source link is dropped.
- **Invite friends:** a short AI-written invite with the activity's picture; one-tap share to WhatsApp, Telegram, X, Facebook or email, or copy for Instagram, Snapchat and TikTok. The real link is added by the code, not the AI.
- **Profile:** saved activities, plus a lookup of city passes and cards that make activities cheaper, linked to official pages only.

## How do I run it?

```bash
pip install -r requirements.txt
echo 'ANTHROPIC_API_KEY=your-key-here' > .env
streamlit run app.py
```

Never commit the `.env` file; it holds the API key and is ignored by git.

## Who did what?

- **Majed:** all technical development — the Python code, Streamlit UI, Claude API integration, budget and filtering logic, and edge cases.
- **Ana:** research and documentation — `docs/research.md` (CBS, Nibud, SCP data), this README, the ethical reflection, the slides and the demo video.
