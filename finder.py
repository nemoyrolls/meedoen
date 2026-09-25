from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

from claude_search import search_json


# Display name -> (emoji, search hints). Only the hints for the categories the
# user picked go into a prompt. The order here is the order the app shows them.
CATEGORIES = {
    "Parties & nightlife": ("🪩", "club nights, student parties, new party concepts, free-entry nights"),
    "Festivals": ("🎪", "festivals, free city festivals, cheap or early-bird festival tickets"),
    "Deals & discounts": ("🏷️", "student discounts, 2-for-1 offers, cheap cinema days, happy hours, CJP deals"),
    "Cheap trips": ("🚆", "cheap train tickets and day trips: NS Dal Voordeel, NS Groepsretour, Spoordeelwinkel, supermarket or drugstore train ticket actions, FlixBus deals"),
    "New in town": ("✨", "new openings, pop-ups, launch events with free entry or an opening offer"),
    "Live music": ("🎸", "concerts, open mics, jam sessions"),
    "Culture": ("🎭", "museums, theatre, film, free museum days"),
    "Sport": ("⚽", "sports clubs, free training sessions, open days, cheap sport with a city pass"),
    "Outdoor": ("🌳", "parks, beach, walks, markets"),
    "Workshops": ("🎨", "courses, workshops, free lessons"),
    "Student": ("🎓", "university and hogeschool event pages, student associations"),
    "Community": ("🤝", "buurthuis, library, volunteering"),
}

# The fun is going somewhere else, so the "stay in the city" rule does not apply,
# and the big national sites are where these deals live.
TRAVEL_CATEGORIES = {"Cheap trips"}
NATIONAL_OK = {"Cheap trips", "Deals & discounts", "Festivals"}


def category_prompt(city, category, max_price, group_size, institution, until, start=None):
    """One short, focused prompt per category. Short prompts are cheap prompts."""
    hints = CATEGORIES[category][1]
    today = date.today().isoformat()

    if category in TRAVEL_CATEGORIES:
        where = (f"Train or bus deals from {city} to somewhere fun, on sale now. "
                 f'"location" is the destination, "price" the ticket per person.')
    else:
        where = f"In {city} or cycling distance of it. Never another city."

    extra = ""
    if category in NATIONAL_OK:
        extra += "Big national sites (NS, festival sites, CJP) are fine here.\n"
    else:
        extra += "Prefer small local sources over the big national listing sites.\n"
    if start and until:
        extra += f"Only between {start.isoformat()} and {until.isoformat()}, or ongoing.\n"
    elif until:
        extra += f"Only on or before {until.isoformat()}, or ongoing.\n"
    if group_size > 1:
        extra += f"They are a group of {group_size}.\n"
    if institution and category == "Student":
        extra += f"They study at {institution}; search its own event pages too.\n"

    return f"""Find up to 3 {category} activities for 18-27 year olds on a low income.
Look for: {hints}.
{where}
Max {max_price} euro per person. Today is {today}; nothing in the past.
Nothing for children, families or over-65s. Search in Dutch, with words like
"studenten", "jongeren", "gratis", "korting".
{extra}
Return ONLY a JSON array. Each object has exactly these keys:
"name", "price" (euro number per person, 0 if free), "date" (YYYY-MM-DD or null if ongoing),
"location", "who_can_join" (copied from the page), "deal" (what makes it cheap, under
12 words, or null), "pass_price" (a lower price with a city pass or CJP, copied like
"Ooievaarspas: €2", or null), "source" (URL of the page).
Copy every price, date and condition from the page. Never estimate. No source, no entry."""


def find_activities(city, categories, max_price, group_size=1, institution=None,
                    until=None, on_progress=None, start=None):
    """Search every picked category at the same time and merge the results.

    Works for any city or gemeente in the Netherlands. Nothing here decides
    whether the user may join or what they pay: budget.py checks that in plain
    Python. on_progress(category, done, total) is called as each one finishes.
    Returns a list of dicts, or None if every search failed.
    """
    chosen = [c for c in categories if c in CATEGORIES]
    if not chosen:
        return []

    found = []
    failures = 0
    pool = ThreadPoolExecutor(max_workers=len(chosen))
    try:
        jobs = {
            pool.submit(
                search_json,
                category_prompt(city, c, max_price, group_size, institution, until, start),
                3,
            ): c
            for c in chosen
        }
        for done, job in enumerate(as_completed(jobs), start=1):
            category = jobs[job]
            result = job.result()
            if result is None:
                failures += 1
            else:
                for item in result:
                    item["category"] = category
                found.extend(result or [])
            if on_progress:
                on_progress(category, done, len(chosen))
    finally:
        # If one search fails hard (no credits), do not start the ones still waiting.
        pool.shutdown(wait=False, cancel_futures=True)

    if failures == len(chosen):
        return None
    return found


if __name__ == "__main__":
    import time
    start = time.time()
    result = find_activities("Den Haag", ["Parties & nightlife", "Cheap trips"], 15,
                             on_progress=lambda c, d, t: print(f"  {d}/{t} {c}"))
    for a in result or []:
        print(a.get("category"), "|", a.get("name"), "|", a.get("price"), "|",
              a.get("date"), "|", a.get("deal"), "|", a.get("pass_price"))
    print(len(result or []), "activities in", round(time.time() - start), "seconds")
