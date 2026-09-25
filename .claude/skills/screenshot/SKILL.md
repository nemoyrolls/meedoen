---
name: screenshot
description: Screenshot any screen of the TagAlong Streamlit app (home, loading, results, profile) with headless Chrome and made-up data - no Chrome MCP, no Claude API calls. Use whenever you need to see or fine-tune the app's design, check a layout or CSS change, or compare desktop and phone widths.
---

# Screenshot the TagAlong app

Do not use the Chrome DevTools MCP for this: the user does not want it driven
repeatedly. This skill uses Chrome's own headless mode instead.

## Take a screenshot

```bash
.claude/skills/screenshot/shot.sh <view> [width] [height]
```

- `view`: `intro` (intro screens; pick one with `STEP=0..3 shot.sh intro`),
  `home` (search page), `loading` (loading screen), `invite` (invite pop-up),
  `results` (cards with sample activities), `profile` (sidebar with saved items and passes),
  `mission` (the Our mission page)
- `width` / `height`: default `1440 1800`. Use `390 1800` for a phone.

It prints the PNG path. Open it with the Read tool to look at it.

## How it works

- `preview_app.py` runs the real `app.py` with sample activities and passes put
  into the session, and fake search functions, so nothing calls the API and the
  loading screen holds still.
- The preview server runs on port 8610 with `runOnSave`, so after editing
  `app.py`, `style.css` or `landing.py` just run `shot.sh` again. If a change to
  another module (finder.py, support.py) is not picked up, stop the server with
  `pkill -f preview_app.py` and run `shot.sh` again.
- The height is the whole capture: Streamlit scrolls inside the page, so make the
  window tall enough (e.g. 2400) to see content lower down.

## Rules

- One or two screenshots per change is enough. Check with the smallest number of shots.
- Sample data lives in `preview_app.py`. Update it when the activity or pass fields change.
- Leave the user's own app on port 8501 alone.
