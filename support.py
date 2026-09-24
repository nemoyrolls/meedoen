import os
from dotenv import load_dotenv
import anthropic
from urllib.parse import urlparse
import json


load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# WHICH LINKS COUNT AS OFFICIAL
#
# This is the only place that decides it. A scheme is thrown away unless its
# link sits on one of these domains (or a subdomain of one). Add a domain here
# when a gemeente or school uses a name we do not guess correctly.
# ---------------------------------------------------------------------------

NATIONAL_DOMAINS = [
    "rijksoverheid.nl",
    "overheid.nl",
    "belastingdienst.nl",
    "toeslagen.nl",
    "duo.nl",
    "svb.nl",
    "uwv.nl",
    "werk.nl",
    "juridischloket.nl",
    "zorgtoeslag.nl",
]

# Gemeente sites are usually gemeentename.nl, which we work out from the
# municipality the user typed. Put the ones that break that rule here.
GEMEENTE_DOMAINS = {
    "den haag": ["denhaag.nl", "ooievaarspas.nl"],
    "the hague": ["denhaag.nl", "ooievaarspas.nl"],
    "rotterdam": ["rotterdam.nl", "rotterdampas.nl"],
    "amsterdam": ["amsterdam.nl", "stadspas.nl"],
}

# Same idea for schools: the domain almost never looks like the full name.
INSTITUTION_DOMAINS = {
    "the hague university of applied sciences": ["dehaagsehogeschool.nl", "hhs.nl"],
    "haagse hogeschool": ["dehaagsehogeschool.nl", "hhs.nl"],
    "thuas": ["dehaagsehogeschool.nl", "hhs.nl"],
    "tu delft": ["tudelft.nl"],
    "leiden university": ["universiteitleiden.nl"],
    "universiteit leiden": ["universiteitleiden.nl"],
    "inholland": ["inholland.nl"],
    "mbo rijnland": ["mborijnland.nl"],
    "roc mondriaan": ["rocmondriaan.nl"],
}


def allowed_domains(municipality, institution=None):
    """Build the list of domains we trust for this search."""
    allowed = list(NATIONAL_DOMAINS)

    key = (municipality or "").strip().lower()
    if key in GEMEENTE_DOMAINS:
        allowed += GEMEENTE_DOMAINS[key]
    else:
        # Reasonable guess: gemeente Delft -> delft.nl and gemeentedelft.nl
        slug = key.replace(" ", "").replace("-", "")
        if slug:
            allowed.append(slug + ".nl")
            allowed.append("gemeente" + slug + ".nl")

    if institution:
        school = institution.strip().lower()
        if school in INSTITUTION_DOMAINS:
            allowed += INSTITUTION_DOMAINS[school]
        else:
            # Fall back to the long words in the name: "TU Delft" -> tudelft.nl
            for word in school.replace("-", " ").split():
                if len(word) >= 4:
                    allowed.append(word + ".nl")

    return allowed


def is_official_link(url, municipality, institution=None):
    """True if this link is on a gemeente, government or school domain."""
    if not isinstance(url, str) or not url.startswith("http"):
        return False

    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return False

    for domain in allowed_domains(municipality, institution):
        if host == domain or host.endswith("." + domain):
            return True
    return False


def find_schemes(municipality, institution=None):
    """Ask Claude to search for support schemes, then keep only the official ones.

    Claude finds and copies. It never says the user qualifies and it never
    makes up a number: plain Python below throws away anything unsourced.
    """
    institution_line = ""
    if institution:
        institution_line = (
            f'- "student": schemes from {institution} itself, such as an emergency fund,\n'
            f"  a hardship fund or a student discount. Search {institution}'s own website.\n"
        )
    else:
        institution_line = (
            '- "student": national schemes for students, such as DUO studiefinanciering.\n'
        )

    prompt = f"""Find money support schemes that a young adult aged 18-27 on a low income
living in the municipality of {municipality}, Netherlands could apply for.

Look for three types:
- "gemeente": schemes from the municipality of {municipality} itself, which depend on
  where the person lives. For example a stadspas, bijzondere bijstand, or a youth fund.
- "national": schemes from the Dutch government that apply everywhere, such as
  zorgtoeslag or huurtoeslag.
{institution_line}
Only use official pages: the gemeente's own website, a government website
(rijksoverheid.nl, belastingdienst.nl, duo.nl and the like), or the school's own site.
Do not use news articles, blogs or advice sites.

Return ONLY a JSON array. No explanation, no markdown, no backticks.
Each object must have exactly these keys:
- "name": the name of the scheme
- "type": exactly one of "gemeente", "national", "student"
- "conditions": a list of short sentences, each starting with "If you".
  For example "If you are between 18 and 27", "If you live in {municipality}".
  Copy the conditions from the page. Keep each one under 12 words.
- "documents": a list of the papers the person has to hand in when they apply.
  An empty list if the page does not say.
- "duration": how long the application takes, copied word for word from the page,
  for example "klaar binnen 8 werkdagen". Use null if the page does not say it.
- "link": the page where you actually apply
- "source": the page where you found this information

Rules you must follow:
- Never write that the user qualifies, is entitled to something, or will receive it.
  You do not know their situation. Only list the conditions from the page.
- Never invent an amount of money, an income limit, or a waiting time.
  If the page does not state it, leave it out or use null.
- If you cannot find an official link, do not include that scheme."""

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                'type': 'web_search_20250305',
                'name': "web_search",
                # Three types to cover, so a few searches each.
                'max_uses': 8
            }]
        )
    except Exception as error:
        print("The search failed:", error)
        return []

    if response.stop_reason == "max_tokens":
        print("The answer was cut off before it was finished.")
        return []

    answer = ''
    for block in response.content:
        if block.type == 'text':
            answer += block.text

    clean = answer.strip()
    if clean.startswith('```'):
        clean = clean.split('```')[1]
        if clean.startswith('json'):
            clean = clean[4:]

    try:
        schemes = json.loads(clean)
    except json.JSONDecodeError:
        print('The AI did not return valid JSON')
        return []

    if not isinstance(schemes, list):
        return []

    return filter_schemes(schemes, municipality, institution)


def filter_schemes(schemes, municipality, institution=None):
    """Throw away anything we cannot send the user to an official page for."""
    kept = []
    for scheme in schemes:
        if not isinstance(scheme, dict):
            continue
        if not is_official_link(scheme.get("link"), municipality, institution):
            continue
        if scheme.get("type") not in ("gemeente", "national", "student"):
            continue
        if not isinstance(scheme.get("conditions"), list):
            continue
        kept.append(scheme)
    return kept


if __name__ == "__main__":
    print("--- link filter ---")
    checks = [
        ("https://www.denhaag.nl/nl/ooievaarspas", "Den Haag", None),
        ("https://www.belastingdienst.nl/zorgtoeslag", "Den Haag", None),
        ("https://www.delft.nl/regelingen", "Delft", None),
        ("https://www.dehaagsehogeschool.nl/noodfonds", "Den Haag",
         "The Hague University of Applied Sciences"),
        ("https://www.blogovergeld.nl/tips", "Den Haag", None),
        ("", "Den Haag", None),
    ]
    for url, muni, inst in checks:
        print(is_official_link(url, muni, inst), "|", url or "(empty)")

    print()
    print("--- find_schemes('Den Haag') ---")
    result = find_schemes("Den Haag")
    for s in result:
        print()
        print(s.get("type").upper(), "|", s.get("name"))
        for c in s.get("conditions", []):
            print("   -", c)
        print("   documents:", s.get("documents"))
        print("   duration:", s.get("duration"))
        print("   apply:", s.get("link"))
    print()
    print(len(result), "schemes kept")
