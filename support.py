from urllib.parse import urlparse

from claude_search import search_json


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
    # Passes that make going out, sport and culture cheaper, run nationally.
    "cjp.nl",
    "jeugdfondssportencultuur.nl",
    "museumkaart.nl",
    "ns.nl",
]

# Gemeente sites are usually gemeentename.nl, which we work out from the
# municipality the user typed. Put the ones that break that rule here.
GEMEENTE_DOMAINS = {
    "den haag": ["denhaag.nl", "ooievaarspas.nl"],
    "the hague": ["denhaag.nl", "ooievaarspas.nl"],
    "rotterdam": ["rotterdam.nl", "rotterdampas.nl"],
    "amsterdam": ["amsterdam.nl", "stadspas.nl"],
    "utrecht": ["utrecht.nl", "u-pas.nl"],
    "leiden": ["leiden.nl", "leidenpas.nl"],
    "delft": ["delft.nl", "delftpas.nl"],
    "groningen": ["gemeente.groningen.nl", "groningen.nl"],
    "eindhoven": ["eindhoven.nl"],
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


def find_passes(municipality, institution=None):
    """Find the passes and cards that make activities cheaper where the user lives.

    Only things that lower the price of going out, sport, culture or travel.
    No income support: this app is about doing fun things, not life admin.
    Claude finds and copies; plain Python below throws away anything that does
    not link to an official page. Returns a list, or None if the search failed.
    """
    school = ""
    if institution:
        school = (f'- "student": what {institution} offers its students for cheaper sport or\n'
                  f"  culture, like a student sports card. Search {institution}'s own site.\n")

    prompt = f"""Which passes or cards make activities cheaper for a young adult (18-27) on a
low income living in {municipality}, Netherlands? Activities means sport, culture,
going out, cinema, festivals and travel. Nothing about income, benefits, rent or debt.

Look for:
- "gemeente": the city pass of {municipality} (like Ooievaarspas in Den Haag, U-pas in
  Utrecht, Rotterdampas, Stadspas Amsterdam) and any local sport or culture fund.
- "national": cards that work everywhere and fit this age, like CJP.
  Skip anything with an age limit below 18.
{school}
Only official pages: the gemeente, the pass's own site, or the school.

Return ONLY a JSON array. Each object has exactly these keys:
"name", "type" (one of "gemeente", "national", "student"),
"perks" (list of up to 4 concrete activity discounts copied from the page, each under
10 words, like "Free swimming at city pools" or "50% off sports club membership"),
"conditions" (list of short "If you ..." sentences copied from the page),
"cost" (what the pass itself costs, copied, or null), "link" (page where you apply).
Never say the user qualifies. Never invent an amount or a limit."""

    passes = search_json(prompt, 4)
    if passes is None:
        return None
    return filter_passes(passes, municipality, institution)


def filter_passes(passes, municipality, institution=None):
    """Throw away anything we cannot send the user to an official page for."""
    kept = []
    for item in passes:
        if not is_official_link(item.get("link"), municipality, institution):
            continue
        if item.get("type") not in ("gemeente", "national", "student"):
            continue
        if not isinstance(item.get("perks"), list) or not item["perks"]:
            continue
        if not isinstance(item.get("conditions"), list):
            item["conditions"] = []
        kept.append(item)
    return kept


if __name__ == "__main__":
    print("--- link filter ---")
    checks = [
        ("https://www.denhaag.nl/nl/ooievaarspas", "Den Haag", None),
        ("https://www.belastingdienst.nl/zorgtoeslag", "Den Haag", None),
        ("https://www.delft.nl/regelingen", "Delft", None),
        ("https://www.dehaagsehogeschool.nl/noodfonds", "Den Haag",
         "The Hague University of Applied Sciences"),
        ("https://www.u-pas.nl/", "Utrecht", None),
        ("https://www.cjp.nl/", "Utrecht", None),
        ("https://www.blogovergeld.nl/tips", "Den Haag", None),
        ("", "Den Haag", None),
    ]
    for url, muni, inst in checks:
        print(is_official_link(url, muni, inst), "|", url or "(empty)")

    print()
    print("--- find_passes('Utrecht') ---")
    result = find_passes("Utrecht") or []
    for p in result:
        print()
        print(p.get("type").upper(), "|", p.get("name"), "|", p.get("cost"))
        for perk in p.get("perks", []):
            print("   +", perk)
        print("   apply:", p.get("link"))
    print()
    print(len(result), "passes kept")
