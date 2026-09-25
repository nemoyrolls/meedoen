import os
import json
import time
import threading
from dotenv import load_dotenv
import anthropic


load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-5"

# Same question within the hour -> same answer, no new API call.
CACHE_SECONDS = 60 * 60
_cache = {}
_cache_lock = threading.Lock()


class OutOfCredits(Exception):
    """The Anthropic account has no credit left. Retrying will not help."""


def search_json(prompt, max_uses):
    """Ask Claude a question it answers with web search, and return the JSON list.

    Returns a list (possibly empty), or None when the call itself failed.
    We use the basic web search tool on purpose. The newer one (web_search_20260209)
    was tested on the same Haarlem search: 47 s, 120K tokens and 0 results, against
    15 s, 52K tokens and 3 results for this one. Low effort means fewer searches.
    """
    prompt += ("\n\nIf you run out of searches, return what you found so far. "
               "Return [] only if you found nothing.")
    with _cache_lock:
        hit = _cache.get(prompt)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    messages = [{"role": "user", "content": prompt}]
    response = None
    try:
        # A long search can pause halfway. Send it back so it can finish.
        for _ in range(3):
            response = client.messages.create(
                model=MODEL,
                max_tokens=8000,
                output_config={"effort": "low"},
                messages=messages,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": max_uses,
                    "user_location": {"type": "approximate", "country": "NL"},
                }],
            )
            if response.stop_reason != "pause_turn":
                break
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content},
            ]
    except anthropic.BadRequestError as error:
        if "credit balance" in str(error):
            raise OutOfCredits() from error
        print("The search failed:", error)
        return None
    except anthropic.APIError as error:
        print("The search failed:", error)
        return None

    if response is None or response.stop_reason in ("max_tokens", "refusal", "pause_turn"):
        print("The search stopped early:", response and response.stop_reason)
        return None

    answer = "".join(block.text for block in response.content if block.type == "text")
    result = parse_json_list(answer)
    if result is None:
        return None

    with _cache_lock:
        _cache[prompt] = (time.time(), result)
    return result


def parse_json_list(answer):
    """Pull the JSON array out of Claude's answer, even if it added words around it."""
    start = answer.find("[")
    end = answer.rfind("]")
    if start == -1 or end < start:
        print("The AI did not return a JSON list")
        return None
    try:
        result = json.loads(answer[start:end + 1])
    except json.JSONDecodeError:
        print("The AI did not return valid JSON")
        return None
    if not isinstance(result, list):
        return None
    return [item for item in result if isinstance(item, dict)]
