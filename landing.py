# The intro screens: a few steps that say what TagAlong does before the search.
# Each headline flips into place like an old split-flap departure board at the station.
# It runs in its own little frame because Streamlit does not run page scripts.
import json

import shapes

INTRO_STEPS = [
    {"sticker": None, "title": "FUN FOR CHEAP",
     "board": "PARTIES · FESTIVALS · TRAINS · DEALS",
     "text": "Nights out, festivals, cheap train trips and deals for 18–27s on a budget, all in one place."},
    {"sticker": "🔗", "title": "REAL LINKS ONLY", "board": None,
     "text": "Every price and date is copied from the real page, with the link. No link, no listing."},
    {"sticker": "🎟️", "title": "PASSES THAT PAY", "board": None,
     "text": "Ooievaarspas, U-pas, CJP: see what your pass takes off. You find it in your profile."},
    {"sticker": "👯", "title": "BRING YOUR CREW", "board": None,
     "text": "See the price for the whole group and share a ready-made invite in one tap."},
]

# Where the shapes sit around each step, so every screen looks a little different.
STEP_SHAPES = [
    [("zigzag", "top:18px;left:4%"), ("dot", "top:40%;right:6%"), ("bolt", "bottom:6px;left:10%;transform:rotate(-10deg)"),
     ("arc", "bottom:14px;right:12%;transform:rotate(-12deg) scale(.85)")],
    [("half_arc", "top:24px;right:9%"), ("triangle", "bottom:18px;left:7%;transform:rotate(-14deg)"),
     ("bolt", "top:30px;left:11%;transform:rotate(14deg) scale(.8)")],
    [("dot", "top:26px;left:8%"), ("zigzag", "bottom:16px;right:5%;transform:rotate(-6deg)"),
     ("half_arc", "bottom:30px;left:14%;transform:rotate(140deg)")],
    [("arc", "top:44px;left:6%;transform:rotate(180deg) scale(.8)"), ("bolt", "bottom:14px;right:9%;transform:rotate(12deg)"),
     ("triangle", "top:34px;right:10%;transform:rotate(-20deg) scale(.8)")],
]

INTRO_HTML = """
<!doctype html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,400;0,700;0,800;1,300;1,400&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; height: 100%; background: transparent; color: #fff; font-family: Poppins, sans-serif; overflow: hidden; }
  .stage { position: relative; height: 100%; display: flex; flex-direction: column; align-items: center;
           justify-content: center; gap: 18px; text-align: center; padding: 0 12px; box-sizing: border-box; }

  .shape { position: absolute; z-index: 0; opacity: 0; animation: pop .6s cubic-bezier(.2,1.5,.4,1) forwards; }
  .shape:nth-child(2) { animation-delay: .15s; } .shape:nth-child(3) { animation-delay: .3s; }
  .shape:nth-child(4) { animation-delay: .45s; }
  @keyframes pop { from { opacity: 0; scale: .3; } to { opacity: 1; scale: 1; } }
  @media (max-width: 640px) { .shape { display: none; } .shape:first-child { display: block; scale: .6; } }
  .content { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; gap: 16px; }

  .logo { display: flex; align-items: center; gap: 12px; opacity: 0;
          animation: logo-in 1s cubic-bezier(.2,.9,.3,1.3) forwards; }
  .logo svg { width: 54px; height: 54px; filter: drop-shadow(0 0 16px rgba(183,209,75,.7)); }
  .logo span { font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 800; letter-spacing: -0.04em; color: #B7D14B;
               text-shadow: 0 0 24px rgba(183,209,75,.5); }
  .logo .ticket { stroke-dasharray: 260; stroke-dashoffset: 260; animation: draw 1.1s .15s ease-out forwards; }
  @keyframes logo-in { 0% { opacity: 0; transform: scale(.6); filter: blur(10px); }
                       100% { opacity: 1; transform: scale(1); filter: blur(0); } }
  @keyframes draw { to { stroke-dashoffset: 0; } }

  .sticker { width: 74px; height: 74px; border-radius: 50%; background: #B7D14B; border: 3px solid #000;
             box-shadow: 5px 5px 0 #F3F3F3; display: flex; align-items: center; justify-content: center;
             font-size: 2.1rem; opacity: 0; animation: pop .55s cubic-bezier(.2,1.5,.4,1) forwards; }

  .board { display: flex; flex-direction: column; align-items: center; gap: 8px; perspective: 700px; }
  .line { display: flex; flex-wrap: wrap; justify-content: center; gap: 0 .5em; }
  .word { display: flex; }
  /* Every letter gets the same width, so the line does not jump while letters spin. */
  .ch { display: inline-block; width: .76em; text-align: center; font-weight: 800;
        color: rgba(255,255,255,.25); transform-origin: 50% 0; }
  .ch.done { animation: flip .45s cubic-bezier(.3,1.4,.5,1); }
  @keyframes flip { 0% { transform: rotateX(-90deg); opacity: .2; } 100% { transform: rotateX(0); opacity: 1; } }
  .line.big { font-size: clamp(2.3rem, 7vw, 4.8rem); line-height: 1.05; }
  .line.big .ch.done { color: #B7D14B; text-shadow: 4px 4px 0 #EFA9CE; }
  .line.small { font-size: clamp(.78rem, 1.7vw, 1.1rem); letter-spacing: .12em; line-height: 1.6; }
  .line.small .ch { width: .84em; }
  .line.small .ch.done { color: #EDEDED; }

  .text { max-width: 520px; font-style: italic; font-weight: 300; font-size: clamp(1rem, 2.2vw, 1.2rem);
          color: #EDEDED; line-height: 1.55; margin: 0; opacity: 0; transform: translateY(8px);
          animation: rise .7s ease-out forwards; animation-delay: var(--text-delay); }
  @keyframes rise { to { opacity: 1; transform: none; } }
</style></head>
<body><div class="stage">
  __SHAPES__
  <div class="content">
    __TOP__
    <div class="board" id="board"></div>
    <p class="text" style="--text-delay: __TEXT_DELAY__s">__TEXT__</p>
  </div>
</div>
<script>
  const LINES = __LINES__;
  const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789€";
  const SWAP_MS = 70, STAGGER_MS = 55, ROW_PAUSE_MS = 300;
  const board = document.getElementById("board");
  const tiles = [];

  LINES.forEach((text, row) => {
    const line = document.createElement("div");
    line.className = "line " + (row === 0 ? "big" : "small");
    text.split(" ").forEach(word => {
      const w = document.createElement("div");
      w.className = "word";
      [...word].forEach(ch => {
        const el = document.createElement("div");
        el.className = "ch";
        w.appendChild(el);
        tiles.push({ el: el, ch: ch, row: row });
      });
      line.appendChild(w);
    });
    board.appendChild(line);
  });

  // Every letter spins through random characters, then flips down into place, left to right.
  const start = performance.now() + __START_MS__;
  tiles.forEach((t, i) => { t.stopAt = start + t.row * ROW_PAUSE_MS + i * STAGGER_MS + Math.random() * 90; t.next = 0; });
  function tick(now) {
    let busy = false;
    for (const t of tiles) {
      if (t.done) continue;
      if (now >= t.stopAt) { t.el.textContent = t.ch; t.el.classList.add("done"); t.done = true; continue; }
      busy = true;
      if (now > start - 400 && now >= t.next) {
        t.el.textContent = CHARS[Math.floor(Math.random() * CHARS.length)];
        t.next = now + SWAP_MS;
      }
    }
    if (busy) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
</script>
</body></html>
"""

LOGO = """<div class="logo">
    <svg viewBox="0 0 64 64" fill="none" stroke="#B7D14B" stroke-width="3.5" stroke-linejoin="round">
      <path class="ticket" d="M8 18h48v8a6 6 0 0 0 0 12v8H8v-8a6 6 0 0 0 0-12z"/>
      <path class="ticket" d="M40 20v24" stroke-dasharray="3 5"/>
    </svg>
    <span>TagAlong</span>
  </div>"""


def intro_html(step):
    """The whole frame for one intro step. Only our own fixed text goes in here."""
    info = INTRO_STEPS[step]
    lines = [info["title"]] + ([info["board"]] if info["board"] else [])
    start_ms = 900 if step == 0 else 350
    # The line of text fades in once the headline has flipped into place.
    text_delay = (start_ms + len(info["title"]) * 55 + 400) / 1000

    top = LOGO if step == 0 else f'<div class="sticker">{info["sticker"]}</div>'
    shape_html = "".join(
        f'<div class="shape" style="{style}">{getattr(shapes, name)()}</div>'
        for name, style in STEP_SHAPES[step]
    )
    return (INTRO_HTML
            .replace("__SHAPES__", shape_html)
            .replace("__TOP__", top)
            .replace("__TEXT__", info["text"])
            .replace("__TEXT_DELAY__", f"{text_delay:.2f}")
            .replace("__START_MS__", str(start_ms))
            .replace("__LINES__", json.dumps(lines)))
