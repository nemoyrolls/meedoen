import os
from dotenv import load_dotenv
import anthropic
from datetime import date 
import json


today = date.today().isoformat()

load_dotenv()


prompt = f"""Find 3 free or cheap activities in The Hague for young people.

Today is {today}. Only include activities on or after this date.

Return ONLY a JSON array. No explanation, no markdown, no backticks.
Each object must have exactly these keys:
- "name": the name of the activity
- "price": price in euros as a number (0 if free)
- "date": the date in YYYY-MM-DD format
- "location": where it takes place
- "source": the URL where you found it

If you cannot find a source URL, do not include that activity."""

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=5000,
    messages=[{"role": "user", "content": prompt}],
    tools=[{
        'type': 'web_search_20250305',
        'name': "web_search",
        'max_uses': 3
    }]
   
)


answer= ''


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
    print ('The AI did not return valid JSON')
    activities = []


def find_activities(city, interests, max_price, group_size):
    today = date.today().isoformat()
    prompt = f'''Find 5 activities in {city} for young people (18-27) interested in {interests}.
Maximum price per person: {max_price} euro.
Today is {today}. Only activities on or after this date.
...rest of your rules...
'''
    return activities


if __name__ == "__main__":
    result = find_activities("The Hague", "music and food", 10, 3)
    for a in result:
        print(a["name"], "-", a["price"], "euro")

