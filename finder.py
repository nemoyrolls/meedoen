import os
from dotenv import load_dotenv
import anthropic
from datetime import date
import json


load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Display name -> search hints. The hints are only put in the prompt for the
# categories the user actually picked, so the search stays focused.
CATEGORIES = {
    "Sport": "sports clubs, free training sessions, open days",
    "Culture": "museums, theatre, free museum days",
    "Music & nightlife": "concerts, open mics, festivals",
    "Student": "university and hogeschool event pages, student associations",
    "Community": "buurthuis, library, volunteering",
    "Outdoor": "parks, beach, walks, markets",
    "Workshops": "courses, workshops, free lessons",
    "Deals & new": "new openings, discounts, special offers",
}


def find_activities(city, categories, max_price, group_size=1, institution=None):
    """Ask Claude to search the web for cheap activities in `city`.

    Works for any city or gemeente in the Netherlands. The user picks the city,
    and the search stays inside it so nobody has to pay for travel.
    categories is a list of keys from CATEGORIES. Returns a list of dicts.
    Nothing here decides whether the user may join or what they pay:
    that is checked in plain Python (budget.py) from the returned numbers.
    """
    chosen = [c for c in categories if c in CATEGORIES]
    if not chosen:
        return []

    today = date.today().isoformat()

    hint_lines = ""
    for name in chosen:
        hint_lines += f"- {name}: {CATEGORIES[name]}\n"

    institution_line = ""
    if institution:
        institution_line = (
            f"The user studies at {institution}. Also search {institution}'s own website "
            f"and event pages for activities open to their students.\n"
        )

    group_line = ""
    if group_size > 1:
        group_line = f"They are coming with {group_size} people in total, so prefer things a small group can join.\n"

    prompt = f"""Find cheap or free activities in {city}, Netherlands for young adults
aged 18-27 on a low income. Everything you return must be something a 20-year-old
would actually turn up to on their own or with friends.

You only get a few web searches, so aim them at this age group from the start.
Write your search terms the way pages for young adults are written: combine the
category words below with words like "studenten", "jongeren", "18+", "gratis",
"korting", "borrel", "proefles", "open mic", "vereniging".
Do not search for "kinderen", "gezin", "familie", "met kinderen" or "kidsproof",
and do not open general "uitjes in {city}" listings. Those pages are written for
families and they will use up your searches for nothing.

Search these categories and nothing else:
{hint_lines}
Rules for what you may return:
- Maximum price {max_price} euro per person.
- Today is {today}. Only activities on or after this date.
- In {city} itself or within walking or cycling distance of it. Never another city:
  travel costs money the user does not have.
- Nothing aimed at children, families with young kids, or over-65s.
{institution_line}{group_line}
Prioritise small, local, overlooked activities: neighbourhood initiatives, buurthuizen,
libraries, student associations, small venues, volunteer groups and local notice boards.
Do not fill the list with the big national event websites. At most one or two well-known
listings; the rest should be things a search engine does not put on the first page.

Aim for about 3 activities per category.

Return ONLY a JSON array. No explanation, no markdown, no backticks.
Each object must have exactly these keys:
- "name": the name of the activity
- "price": price in euros as a number, per person (0 if free)
- "date": the date in YYYY-MM-DD format, or null if it is ongoing or anytime
- "location": where it takes place
- "category": exactly one of these strings: {", ".join(chosen)}
- "who_can_join": who is allowed to join, copied from the page. For example
  "Only for THUAS students", "Members only", "Open to everyone"
- "source": the URL where you found it

Copy the price from the page. Never estimate a price, a date or a condition.
If you cannot find a source URL, do not include that activity."""

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                'type': 'web_search_20250305',
                'name': "web_search",
                'max_uses': 2 * len(chosen)
            }]
        )
    except Exception as error:
        print("The search failed:", error)
        return []

    if response.stop_reason == "max_tokens":
        print("The answer was cut off before it was finished. Try fewer categories.")
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
        activities = json.loads(clean)
    except json.JSONDecodeError:
        print('The AI did not return valid JSON')
        return []

    if not isinstance(activities, list):
        return []
    return activities


if __name__ == "__main__":
    print("--- test 1: one category ---")
    result = find_activities("Den Haag", ["Culture"], 10)
    for a in result:
        print(a.get("category"), "|", a.get("name"), "|", a.get("price"), "euro |",
              a.get("date"), "|", a.get("who_can_join"))
    print(len(result), "activities")

    print()
    print("--- test 2: two categories, with institution and group ---")
    result = find_activities("Den Haag", ["Sport", "Student"], 5,
                             group_size=3, institution="The Hague University of Applied Sciences")
    for a in result:
        print(a.get("category"), "|", a.get("name"), "|", a.get("price"), "euro |",
              a.get("date"), "|", a.get("who_can_join"))
    print(len(result), "activities")
