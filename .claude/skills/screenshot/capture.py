"""Take one screenshot of a page with headless Chrome, after waiting for it to draw.

Chrome's own --screenshot flag fires on page load, before Streamlit has drawn
anything, so this talks to Chrome's debugging port directly and waits first.
Usage: capture.py URL OUT.png WIDTH HEIGHT [WAIT_SECONDS]
"""
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

from websockets.sync.client import connect

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9333

url, out, width, height = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
wait = float(sys.argv[5]) if len(sys.argv) > 5 else 6

profile = tempfile.mkdtemp(prefix="tagalong-chrome-")
chrome = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
     f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
     f"--window-size={width},{height}", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)

try:
    target = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list") as r:
                target = next(t for t in json.load(r) if t["type"] == "page")
            break
        except Exception:
            time.sleep(0.25)
    if not target:
        sys.exit("Chrome did not start")

    with connect(target["webSocketDebuggerUrl"], max_size=None) as ws:
        counter = [0]

        def send(method, **params):
            counter[0] += 1
            ws.send(json.dumps({"id": counter[0], "method": method, "params": params}))
            while True:
                message = json.loads(ws.recv())
                if message.get("id") == counter[0]:
                    return message.get("result", {})

        send("Emulation.setDeviceMetricsOverride", width=width, height=height,
             deviceScaleFactor=1, mobile=width < 600)
        send("Page.navigate", url=url)
        time.sleep(wait)
        shot = send("Page.captureScreenshot", format="png")
        with open(out, "wb") as f:
            f.write(base64.b64decode(shot["data"]))
finally:
    chrome.terminate()
    chrome.wait(timeout=5)

print(out)
