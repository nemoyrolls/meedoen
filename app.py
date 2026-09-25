import os
import html
from datetime import date, timedelta
import streamlit as st
from urllib.parse import quote
from dotenv import load_dotenv


st.set_page_config(page_title="TagAlong", page_icon="🎟️", layout="wide",
                   initial_sidebar_state="auto")

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    st.title("TagAlong")
    st.error(
        "No API key found. Copy .env.example to .env and put your "
        "ANTHROPIC_API_KEY in it, then start the app again."
    )
    st.stop()

import anthropic
from claude_search import client, MODEL, OutOfCredits
from finder import find_activities, CATEGORIES
from support import find_passes
from budget import filter_activities
from images import add_images
from landing import intro_html, INTRO_STEPS
import shapes


HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def make_invite(activity, group_size, city):
    """Write a short message the user can send to friends. No web search."""
    when = activity.get("date") or "whenever you want"
    price = activity.get("price")
    price_text = "it is free" if price == 0 else f"it costs {price} euro each"

    prompt = f"""Write a short message inviting friends to this activity, to send in a
group chat or post on social media.

Activity: {activity.get('name')}
Where: {activity.get('location')} in {city}
When: {when}
Price: {price_text}
People coming: {group_size}

Keep it under 40 words. Friendly and casual, the way a 22-year-old writes to
friends. Mention the price, because money is the reason they might say no.
Do not invent any detail that is not above. Do not add a link: we add the real
link after your message. Return only the message itself, nothing else."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}]
        )
    except anthropic.BadRequestError as error:
        if "credit balance" in str(error):
            raise OutOfCredits() from error
        return None
    except Exception:
        return None

    if response.stop_reason == "max_tokens":
        return None

    text = ''
    for block in response.content:
        if block.type == 'text':
            text += block.text
    return text.strip() or None


def travel_note(home_place, city, has_student_ov):
    """Warn when the activities are not in the user's own town.

    We never state a fare. We do not know what the journey costs and we are
    not going to guess it at someone who cannot afford to be wrong.
    """
    if not home_place:
        return None
    if home_place.strip().lower() == city.strip().lower():
        return None

    note = (
        f"These activities are in {city}, and you live in {home_place.strip()}. "
        "The prices below do not include getting there and back."
    )
    if has_student_ov:
        note += (
            " You said you have a student travel product. Check whether this day "
            "falls in your free travel days (weekdays or weekend) before you go."
        )
    return note


# ------------------------------------------------------------------- helpers

PICK_DATES = "📅 Pick dates"
WHEN = {
    "This weekend": 3,
    "Next 2 weeks": 14,
    "This month": 31,
    "Any time": None,
    PICK_DATES: None,
}

CREDITS_MESSAGE = (
    "TagAlong's AI credits have run out, so we can't search right now. "
    "(For the team: top up the Anthropic account under Plans & Billing.)"
)

LOADING_EMOJI = ["⚽", "🎸", "🪩", "🎪", "🚆", "🏀", "🎭", "🛹"]


def esc(value):
    return html.escape(str(value or ""))


def euro(amount):
    return f"€{amount:.2f}".replace(".00", "")


def nice_date(value):
    """2026-09-26 -> Sat 26 Sep. budget.py already checked the format."""
    if not value:
        return "Ongoing"
    return date.fromisoformat(value).strftime("%a %d %b")


def activity_key(activity):
    return str(abs(hash((activity.get("source"), activity.get("name")))))


def pic_html(activity):
    """The picture on top of a card: the page's own photo over a gradient + emoji,
    so there is always something to see if the photo is missing or blocked."""
    price = activity.get("price", 0)
    if price == 0:
        badge = '<span class="price free">Free</span>'
    else:
        badge = f'<span class="price">{euro(price)}</span>'

    emoji = CATEGORIES.get(activity.get("category"), ("🎟️",))[0]
    picture = ""
    if activity.get("image"):
        picture = (f'<img src="{esc(activity["image"])}" alt="" loading="lazy" '
                   f'referrerpolicy="no-referrer">')
    return (f'<div class="pic">{emoji}{picture}'
            f'<span class="chip">📅 {esc(nice_date(activity.get("date")))}</span>{badge}</div>')


def card_html(activity, people):
    price = activity.get("price", 0)
    lines = f'<div class="meta">📍 {esc(activity.get("location"))}</div>'
    if activity.get("deal"):
        lines += f'<div class="deal">🏷️ {esc(activity["deal"])}</div>'
    if activity.get("pass_price"):
        lines += f'<div class="pass">🎟️ {esc(activity["pass_price"])}</div>'
    if activity.get("who_can_join"):
        lines += f'<div class="meta">👥 {esc(activity["who_can_join"])}</div>'
    if people > 1 and price:
        lines += f'<div class="meta">{euro(price * people)} for {people} people</div>'

    return (
        '<div class="card">'
        f'{pic_html(activity)}'
        '<div class="body">'
        f'<div class="title">{esc(activity.get("name"))}</div>'
        f'{lines}'
        f'<a class="go" href="{esc(activity.get("source"))}" target="_blank" rel="noopener">Check it out</a>'
        '</div></div>'
    )


def loading_html(done, total, last):
    """One emoji at a time above an always-green striped bar."""
    emoji = "".join(f"<span>{e}</span>" for e in LOADING_EMOJI)
    percent = int(100 * done / total) if total else 0
    status = f"Found {last} ✓" if last else "Warming up the search..."
    return (
        '<div class="loading">'
        f'<div class="emoji">{emoji}</div>'
        '<h3>Finding cheap fun</h3>'
        f'<div class="bar"><div style="width:{max(percent, 12)}%"></div></div>'
        f'<p>{esc(status)} · {done} of {total} done</p>'
        '</div>'
    )


state = st.session_state
state.setdefault("view", "home")
state.setdefault("saved", {})



# ------------------------------------------------------------------ profile
# The profile has two faces: a full page in the middle (Profile in the top bar),
# and a compact summary in the sidebar on every other page.

def look_up_passes(municipality):
    with st.spinner("Checking official pages..."):
        try:
            state["pass_results"] = find_passes(municipality, state.get("institution"))
        except OutOfCredits:
            state["pass_results"] = "credits"
        except Exception:
            state["pass_results"] = None
        state["passes_for"] = municipality


def passes_html(passes):
    cards = ""
    for item in passes:
        perks = "".join(f"<li>{esc(p)}</li>" for p in item.get("perks", []))
        cost = f'<div class="small">Pass costs: {esc(item["cost"])}</div>' if item.get("cost") else ""
        conditions = " · ".join(esc(c) for c in item.get("conditions", [])[:3])
        cards += (f'<div class="passcard"><b>{esc(item.get("name"))}</b><ul>{perks}</ul>{cost}'
                  f'<div class="small">{conditions}</div>'
                  f'<a href="{esc(item.get("link"))}" target="_blank" rel="noopener">Get it ⟶</a></div>')
    return f'<div class="passgrid">{cards}</div>'


def show_pass_results():
    if "pass_results" not in state:
        return
    passes = state["pass_results"]
    if passes == "credits":
        st.error(CREDITS_MESSAGE)
    elif passes is None:
        st.error("That lookup did not work just now. Try again in a minute.")
    elif not passes:
        st.info("No passes with an official page came back. Check your gemeente's site for a 'stadspas'.")
    else:
        st.markdown(passes_html(passes), unsafe_allow_html=True)
        st.caption("Found by AI from official pages. Only the official page can say if you can get it.")


def profile_page():
    st.markdown(shapes.decoration("profile"), unsafe_allow_html=True)
    saved = state["saved"]
    st.markdown(
        f'<div class="profile-hero"><div class="avatar big">{shapes.avatar()}</div>'
        f'<div><h1>Your profile</h1><p>{len(saved)} saved · your passes & discounts</p></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<h2 class="profile-title">♥ Saved</h2>', unsafe_allow_html=True)
    if not saved:
        st.markdown(
            '<div class="empty small"><p>Nothing saved yet. Tap ♡ Save on anything you like '
            'and it lands here.</p></div>', unsafe_allow_html=True)
        left, middle, right = st.columns([2, 1.2, 2])
        with middle:
            st.page_link(DISCOVER, label="Find something fun ⟶", use_container_width=True)
    else:
        activity_grid(list(saved.values()), state.get("q", {}).get("people", 1), saved_view=True)

    st.markdown('<h2 class="profile-title">🎟️ Passes that save you money</h2>'
                '<p class="profile-sub">City passes and cards that make sport, culture and going out cheaper.</p>',
                unsafe_allow_html=True)
    with st.container(key="passbox"):
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            municipality = st.text_input("Your gemeente", state.get("passes_for") or state.get("city", "Den Haag"))
        with col2:
            if st.button("Show my passes", type="primary", use_container_width=True) and municipality.strip():
                look_up_passes(municipality.strip())
    show_pass_results()


def profile_sidebar():
    """The short version for the sidebar, with a way into the full page."""
    saved = state["saved"]
    st.markdown(
        f'<div class="profile-head"><div class="avatar">{shapes.avatar()}</div>'
        f'<div><b>Your profile</b><span>{len(saved)} saved · passes & discounts</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### ♥ Saved")
    if not saved:
        st.caption("Tap ♡ Save on anything you like and it lands here.")
    for activity in list(saved.values())[:3]:
        price = activity.get("price", 0)
        st.markdown(
            f'<div class="saved"><a href="{esc(activity.get("source"))}" target="_blank" rel="noopener">'
            f'{esc(activity.get("name"))}</a>'
            f'<span>{"Free" if price == 0 else euro(price)} · {esc(nice_date(activity.get("date")))}</span></div>',
            unsafe_allow_html=True,
        )
    if len(saved) > 3:
        st.caption(f"and {len(saved) - 3} more")

    st.markdown("#### 🎟️ Your passes")
    passes = state.get("pass_results")
    if isinstance(passes, list) and passes:
        st.caption(" · ".join(p.get("name", "") for p in passes))
    else:
        st.caption("See which city passes and cards make activities cheaper where you live.")
    st.page_link(PROFILE, label="Open my profile ⟶", use_container_width=True)


# ---------------------------------------------------------------- home page

def search_form():
    """The search box. Not an st.form, so the calendar can open the moment
    someone picks "Pick dates"."""
    with st.container(key="search"):
        categories = st.pills(
            "Mood",
            options=list(CATEGORIES.keys()),
            format_func=lambda c: f"{CATEGORIES[c][0]} {c}",
            default=state.get("q", {}).get("categories", ["Parties & nightlife", "Festivals", "Deals & discounts"]),
            selection_mode="multi",
            label_visibility="collapsed",
        )
        col1, col2, col3 = st.columns([1.3, 1.3, 0.9])
        with col1:
            city = st.text_input("📍 City", state.get("city", "Den Haag"))
        with col2:
            max_price = st.slider("💶 Max per person", 0, 50, 10, format="€%d")
        with col3:
            group_size = st.number_input("👯 How many?", min_value=1, value=1, step=1)

        when_label = st.segmented_control("📅 When", list(WHEN.keys()), default="Next 2 weeks")
        start, until = date.today(), None
        if when_label == PICK_DATES:
            today = date.today()
            picked = st.date_input(
                "Your dates",
                value=(today, today + timedelta(days=7)),
                min_value=today,
                max_value=today + timedelta(days=365),
                format="DD/MM/YYYY",
            )
            # While someone is still clicking, the range has only its first day.
            start = picked[0] if picked else today
            until = picked[1] if len(picked) > 1 else start
            if len(picked) > 1:
                days = (until - start).days + 1
                summary = (f"📅 {nice_date(start.isoformat())} → {nice_date(until.isoformat())}"
                           f" · {days} day{'s' if days != 1 else ''}")
            else:
                summary = f"📅 {nice_date(start.isoformat())} → now pick your last day"
            st.markdown(f'<div class="date-summary">{esc(summary)}</div>', unsafe_allow_html=True)
        else:
            days = WHEN.get(when_label or "Any time")
            until = start + timedelta(days=days) if days else None

        with st.expander("More about you (optional)"):
            home_place = st.text_input("Where do you live?", "")
            institution = st.text_input("Where do you study?", "")
            has_student_ov = st.checkbox("I have a studentenreisproduct")

        go = st.button("Find something fun ⟶", type="primary", use_container_width=True)

    if go:
        if not city.strip():
            st.warning("Fill in a city first.")
        elif not categories:
            st.warning("Pick at least one thing you're up for.")
        else:
            state["q"] = {
                "city": city.strip(),
                "categories": categories,
                "max_price": max_price,
                "start": start,
                "until": until,
                "when_label": when_label or "Any time",
                "people": int(group_size),
                "institution": institution.strip() or None,
            }
            state["city"] = city.strip()
            state["institution"] = institution.strip() or None
            state["travel"] = travel_note(home_place or None, city, has_student_ov)
            state["view"] = "loading"
            st.rerun()


def home_page():
    st.markdown(shapes.decoration("home"), unsafe_allow_html=True)
    st.markdown(
        '<div class="search-head"><span class="brand">🎟️ TagAlong</span>'
        '<h1>What are you up for?</h1>'
        '<p>Pick your vibe, city, budget and dates. We search the web right now.</p></div>',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns([1, 6, 1])
    with middle:
        search_form()
        if st.button("↺ How it works", type="tertiary"):
            state["onboarded"] = False
            state["intro_step"] = 0
            st.rerun()
    st.markdown(
        '<div class="mission">'
        '<div class="section-label">Our mission</div>'
        '<h2>Nobody should stay home because going out costs too much.</h2>'
        '<p>Lots of 18 to 27 year olds on a low income skip nights out, sport and festivals '
        'with friends because of money. At the same time, the discounts and city passes made '
        'for exactly them go unused, because nobody tells them they exist. '
        'TagAlong puts both in one place.</p></div>'
        '<div class="features">'
        '<div class="feature"><b>🔎 Finds the cheap stuff</b><span>A live search for parties, festivals, '
        'train deals and free events near you, within your budget.</span></div>'
        '<div class="feature"><b>🎟️ Shows what your pass gives</b><span>Ooievaarspas, U-pas, CJP: see which '
        'discounts you might get, with the official page to check.</span></div>'
        '<div class="feature"><b>🔗 Never guesses</b><span>Every price and date comes from a real page '
        'with a link. No link, no listing.</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns([2, 1, 2])
    with middle:
        st.page_link(MISSION, label="Read the full story ⟶", use_container_width=True)


# ------------------------------------------------------------- loading page

def loading_page():
    q = state["q"]
    screen = st.empty()
    screen.markdown(loading_html(0, len(q["categories"]), None), unsafe_allow_html=True)

    def progress(category, done, total):
        screen.markdown(loading_html(done, total, category), unsafe_allow_html=True)

    try:
        found = find_activities(
            q["city"], q["categories"], q["max_price"],
            group_size=q["people"], institution=q["institution"],
            until=q["until"], start=q.get("start"), on_progress=progress,
        )
        state.pop("error", None)
    except OutOfCredits:
        found = None
        state["error"] = "credits"
    except Exception:
        found = None
        state.pop("error", None)

    if found is None:
        state["activities"] = None
    else:
        kept = filter_activities(found, q["max_price"], q["until"], q.get("start"))
        state["activities"] = add_images(kept)
        state["found_count"] = len(found)
    state.pop("filter", None)
    state["view"] = "results"
    st.rerun()


# ------------------------------------------------------------- results page

def share_links_html(activity, message):
    """One-tap share buttons. The link to the real page is always added by us."""
    source = activity.get("source") or ""
    text = f"{message}\n{source}".strip()
    links = [
        ("💬", "WhatsApp", f"https://wa.me/?text={quote(text)}"),
        ("✈️", "Telegram", f"https://t.me/share/url?url={quote(source)}&text={quote(message)}"),
        ("𝕏", "X", f"https://twitter.com/intent/tweet?text={quote(text)}"),
        ("👍", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={quote(source)}"),
        ("✉️", "Email", f"mailto:?subject={quote(activity.get('name') or 'Join me?')}&body={quote(text)}"),
    ]
    buttons = "".join(
        f'<a class="share" href="{esc(url)}" target="_blank" rel="noopener">{icon} {name}</a>'
        for icon, name, url in links
    )
    return f'<div class="shares">{buttons}</div>'


@st.dialog("Tag your crew along", width="medium")
def invite_dialog(activity):
    people = state.get("q", {}).get("people", 1)
    price = activity.get("price", 0)
    group = f" · {euro(price * people)} for {people}" if people > 1 and price else ""
    st.markdown(
        f'<div class="invite-card">{pic_html(activity)}'
        f'<div class="body"><div class="title">{esc(activity.get("name"))}</div>'
        f'<div class="meta">📍 {esc(activity.get("location"))}{esc(group)}</div></div></div>',
        unsafe_allow_html=True,
    )

    key = "invite-" + activity_key(activity)
    if key not in state:
        with st.spinner("Writing your invite..."):
            try:
                state[key] = make_invite(activity, people, state.get("q", {}).get("city", ""))
            except OutOfCredits:
                state[key] = None
                st.error(CREDITS_MESSAGE)
                return
    message = state[key]
    if not message:
        st.error("Could not write the message just now. Try again.")
        state.pop(key, None)
        return

    st.markdown('<div class="section-label left">Share it</div>', unsafe_allow_html=True)
    st.markdown(share_links_html(activity, message), unsafe_allow_html=True)
    st.caption("Or copy it for Instagram, Snapchat or TikTok (button in the corner):")
    st.code(f"{message}\n{activity.get('source') or ''}".strip(), language=None, wrap_lines=True)


def results_page():
    st.markdown(shapes.decoration("results"), unsafe_allow_html=True)
    q = state["q"]
    activities = state.get("activities")

    col1, col2 = st.columns([5, 1], vertical_alignment="center")
    with col1:
        until = ""
        if q["until"] and q.get("start") and q["start"] > date.today():
            until = f" · {q['start'].strftime('%d %b')} – {q['until'].strftime('%d %b')}"
        elif q["until"]:
            until = f" · until {q['until'].strftime('%d %b')}"
        st.markdown(
            '<div class="topbar"><span class="brand">🎟️ TagAlong</span>'
            f'<span class="summary">{esc(q["city"])} · max {euro(q["max_price"])} pp{until}</span></div>',
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("⟵ New search", use_container_width=True):
            state["view"] = "home"
            st.rerun()

    if state.get("travel"):
        st.info(state["travel"])

    if activities is None:
        if state.get("error") == "credits":
            st.error(CREDITS_MESSAGE)
        else:
            st.error("The search did not work just now. Try again in a minute.")
        return
    if not activities:
        tip = ("We found some things, but none survived the check on price, date and source link."
               if state.get("found_count") else "Nothing came back this time.")
        st.markdown(
            f'<div class="empty"><h3>Nothing yet</h3><p>{tip}<br>'
            'Try a higher budget, a longer time window or another vibe.</p></div>',
            unsafe_allow_html=True,
        )
        return

    present = [c for c in CATEGORIES if any(a.get("category") == c for a in activities)]
    choice = st.pills(
        "Show", ["All"] + present, default="All", key="filter",
        format_func=lambda c: "✦ All" if c == "All" else f"{CATEGORIES[c][0]} {c}",
        label_visibility="collapsed",
    )
    shown = [a for a in activities if choice in (None, "All") or a.get("category") == choice]
    st.caption(f"{len(shown)} things, cheapest first. Always check the link before you go.")

    activity_grid(shown, q["people"])


def activity_grid(items, people, saved_view=False):
    """Cards in rows of three, each with its buttons. Row by row, so every row lines up."""
    for row_start in range(0, len(items), 3):
        columns = st.columns(3)
        for column, activity in zip(columns, items[row_start:row_start + 3]):
            key = activity_key(activity)
            with column:
                st.markdown(card_html(activity, people), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                with b1:
                    is_saved = key in state["saved"]
                    if saved_view:
                        label = "✕ Remove"
                    else:
                        label = "♥ Saved" if is_saved else "♡ Save"
                    if st.button(label, key=f"save-{key}", use_container_width=True):
                        if is_saved:
                            state["saved"].pop(key, None)
                        else:
                            state["saved"][key] = activity
                        st.rerun()
                with b2:
                    if st.button("💬 Invite", key=f"invite-btn-{key}", use_container_width=True):
                        invite_dialog(activity)
        st.write("")


# ------------------------------------------------------------- mission page

def mission_page():
    st.markdown(shapes.decoration("mission"), unsafe_allow_html=True)
    st.markdown(
        '''<div class="prose"><div class="prose">
<div class="section-label">Our mission</div>
<h1>Fun for everyone,<br>not just for who can pay.</h1>
<p class="lead">TagAlong helps young people on a low income go out with their friends,
and find the discounts that were made for them.</p>

<section class="block"><div class="block-head"><span class="sticker">😬</span><h3>The problem</h3></div>
<p>For a lot of 18 to 27 year olds in the Netherlands, money decides whether they can join in.
A concert, a festival ticket, a sports club or a train ride to see friends: when the budget is
tight, these are the first things to go. Saying no again and again slowly pushes people out of
their social life.</p>
<p>The strange part: there is help meant for exactly this. City passes like the Ooievaarspas in
Den Haag or the U-pas in Utrecht, CJP, student deals, free festivals and off-peak train offers.
Much of it goes unused, simply because people do not know it exists or cannot find it.</p>
</section>
<section class="block"><div class="block-head"><span class="sticker">🙋</span><h3>Who we built it for</h3></div>
<p>Think of Maya. She is 21, studies in Den Haag and lives on a tight monthly budget. Her friends
ask her out, and she often says no because she cannot afford it. She has never heard which
youth discounts her city offers. TagAlong is for Maya.</p>
</section>
<section class="block"><div class="block-head"><span class="sticker">🔎</span><h3>What TagAlong does</h3></div>
<ul>
<li><b>Searches live.</b> You pick what you are up for, your city, your budget and when.
TagAlong searches the web right now for parties, festivals, cheap trips, deals and free events.</li>
<li><b>Checks every result.</b> Plain code, not the AI, throws out anything without a source link,
anything over your budget and anything in the past.</li>
<li><b>Shows your passes.</b> In your profile you see which passes and cards make activities
cheaper where you live, and what they take off.</li>
<li><b>Gets your friends along.</b> See the price for the whole group and share a ready-made
invite on WhatsApp, Telegram, X, Facebook or email in one tap.</li>
</ul>
</section>
<section class="block"><div class="block-head"><span class="sticker">🔗</span><h3>Our one hard rule</h3></div>
<p>The AI never states a price, a date or who can join from memory. Everything is copied from a
real page, and every result links to that page. If there is no source, it does not show up.
We never tell you that you qualify for a pass: only the official page can say that.
Wrong information hurts most the people who cannot afford a mistake, so when in doubt,
we leave it out.</p>
</section>
<section class="block"><div class="block-head"><span class="sticker">🌍</span><h3>Why it matters</h3></div>
<p>TagAlong works on the United Nations Sustainable Development Goal 10, <i>reduced inequalities</i>,
target 10.2: social inclusion of all, regardless of economic status. Being able to join your
friends should not depend on your bank balance.</p>
</section>
<section class="block"><div class="block-head"><span class="sticker">💡</span><h3>Good to know</h3></div>
<p>AI can still make mistakes. Always open the link and check the price and date before you go
or pay. TagAlong has no accounts: your saved items disappear when you close the page.</p>
</section>
<p class="credits">Made by Majed Al-Sakkaf and Ana Talg Wolf for Hackathon 3, AI for Good.
Built with Python, the Claude API and Streamlit.</p>
</div>''',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns([2, 1.2, 2])
    with middle:
        st.page_link(DISCOVER, label="Find something fun ⟶", use_container_width=True)


# --------------------------------------------------------------- intro page

def intro_page():
    step = state.get("intro_step", 0)
    last = len(INTRO_STEPS) - 1
    st.iframe(intro_html(step), height=430)

    dots = "".join(f'<span class="{"on" if i == step else ""}"></span>' for i in range(last + 1))
    st.markdown(f'<div class="dots">{dots}</div>', unsafe_allow_html=True)

    if step == 0:
        left, next_col, right = st.columns([2, 1.3, 2])
    else:
        left, back_col, next_col, right = st.columns([1.6, 1, 1.3, 1.6])
        with back_col:
            if st.button("⟵ Back", use_container_width=True):
                state["intro_step"] = step - 1
                st.rerun()
    with next_col:
        label = "Let's go ⟶" if step == last else "Next ⟶"
        if st.button(label, type="primary", use_container_width=True):
            if step == last:
                state["onboarded"] = True
            else:
                state["intro_step"] = step + 1
            st.rerun()
    left, middle, right = st.columns([2, 1, 2])
    with middle:
        if step < last and st.button("Skip intro", type="tertiary", use_container_width=True):
            state["onboarded"] = True
            st.rerun()


# -------------------------------------------------------------------- router

def discover_page():
    if not state.get("onboarded"):
        intro_page()
    elif state["view"] == "loading" and "q" in state:
        loading_page()
    elif state["view"] == "results" and "q" in state:
        results_page()
    else:
        home_page()


DISCOVER = st.Page(discover_page, title="Discover", icon=":material/explore:", default=True)
PROFILE = st.Page(profile_page, title="Profile", icon=":material/person:", url_path="profile")
MISSION = st.Page(mission_page, title="Our mission", icon=":material/favorite:", url_path="mission")
page = st.navigation([DISCOVER, PROFILE, MISSION], position="top")

# On the profile page the profile is in the middle, so the sidebar does not repeat it.
if page.url_path != PROFILE.url_path:
    with st.sidebar:
        profile_sidebar()

page.run()
