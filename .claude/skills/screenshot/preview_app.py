"""Runs the real app.py with made-up data, so every screen can be screenshotted
without calling the Claude API. Pick the screen with ?view=home|loading|results|profile|mission|invite, or
?view=intro&step=0..3 for the intro screens.
"""
import os
import sys
import time
from datetime import date, timedelta

import streamlit as st

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT)
os.chdir(PROJECT)
os.environ.setdefault("ANTHROPIC_API_KEY", "preview-no-calls")

import finder
import support

SAMPLE = [
    {"name": "Free Friday: Student Night", "price": 0, "date": (date.today() + timedelta(days=2)).isoformat(),
     "location": "Paard, Den Haag", "category": "Parties & nightlife", "who_can_join": "18+, student ID",
     "deal": "Free entry before 23:00", "pass_price": None, "source": "https://example.com/a",
     "image": "https://picsum.photos/seed/party/640/360"},
    {"name": "Silent disco on the beach", "price": 7.5, "date": (date.today() + timedelta(days=9)).isoformat(),
     "location": "Scheveningen", "category": "Parties & nightlife", "who_can_join": "Open to everyone",
     "deal": None, "pass_price": "Ooievaarspas: €3", "source": "https://example.com/b", "image": None},
    {"name": "Haagse Kermis Festival", "price": 5, "date": (date.today() + timedelta(days=10)).isoformat(),
     "location": "Malieveld", "category": "Festivals", "who_can_join": "Open to everyone",
     "deal": "Early bird tickets", "pass_price": None, "source": "https://example.com/c",
     "image": "https://picsum.photos/seed/festival/640/360"},
    {"name": "Day ticket anywhere in NL", "price": 9, "date": None, "location": "Maastricht (from Den Haag)",
     "category": "Cheap trips", "who_can_join": "Everyone", "deal": "Off-peak only, drugstore action",
     "pass_price": None, "source": "https://example.com/d", "image": "https://picsum.photos/seed/train/640/360"},
]

SAMPLE_PASSES = [
    {"name": "Ooievaarspas", "type": "gemeente", "cost": "Free",
     "perks": ["Free swimming at city pools", "Cheap sports club membership", "Discount on cinema"],
     "conditions": ["If you live in Den Haag", "If your income is low"], "link": "https://www.denhaag.nl/"},
    {"name": "CJP", "type": "national", "cost": "€17,50 a year",
     "perks": ["Discount on festivals and concerts", "Cheaper museum tickets"],
     "conditions": ["If you are under 30"], "link": "https://www.cjp.nl/"},
]

view = st.query_params.get("view", "home")
state = st.session_state

if "seeded" not in state:
    state["seeded"] = True
    state["onboarded"] = view != "intro"
    state["intro_step"] = int(st.query_params.get("step", 0))
    q = {"city": "Den Haag", "categories": ["Parties & nightlife", "Festivals", "Cheap trips"],
         "max_price": 10, "until": date.today() + timedelta(days=14), "when_label": "Next 2 weeks",
         "people": 3, "institution": None}
    if view in ("results", "loading", "invite"):
        state["q"] = q
        state["view"] = "results" if view == "invite" else view
        state["activities"] = list(SAMPLE)
        state["found_count"] = len(SAMPLE)
    if view == "profile":
        state["saved"] = {str(i): a for i, a in enumerate(SAMPLE[:3])}
        state["pass_results"] = SAMPLE_PASSES


# The loading screen never finishes in the preview: it just holds still.
def slow_search(*args, on_progress=None, **kwargs):
    if on_progress:
        on_progress("Festivals", 1, 3)
    time.sleep(120)
    return []


finder.find_activities = slow_search
support.find_passes = lambda *a, **k: SAMPLE_PASSES

APP = os.path.join(PROJECT, "app.py")
app = {"__file__": APP, "__name__": "__main__"}
exec(compile(open(APP).read(), APP, "exec"), app)

# Open the invite pop-up with a ready message, so no API call is needed.
if view == "invite":
    activity = SAMPLE[0]
    state["invite-" + app["activity_key"](activity)] = (
        "Free student night at Paard this Friday 🎉 Free entry before 23:00, "
        "so it costs us nothing. Who's in?")
    app["invite_dialog"](activity)
