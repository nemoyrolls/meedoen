#!/bin/bash
# Screenshot a screen of the TagAlong app with headless Chrome. No MCP, no API calls.
# Usage: shot.sh [intro|home|loading|results|profile|mission|invite] [width] [height]
# For intro, set STEP=0..3 (default 0).
# Prints the path of the PNG it wrote.
set -e

VIEW="${1:-home}"
WIDTH="${2:-1440}"
HEIGHT="${3:-1800}"
PORT=8610
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
OUT_DIR="${TMPDIR:-/tmp}/tagalong-shots"
OUT="$OUT_DIR/$VIEW${STEP:+-$STEP}-${WIDTH}x${HEIGHT}.png"
mkdir -p "$OUT_DIR"

# Start the preview server once; it restarts itself when app files change.
if ! curl -s -o /dev/null "http://localhost:$PORT"; then
  (cd "$PROJECT" && nohup venv/bin/streamlit run "$HERE/preview_app.py" \
      --server.headless true --server.port $PORT --server.runOnSave true \
      > "$OUT_DIR/server.log" 2>&1 &)
  for _ in $(seq 1 30); do
    curl -s -o /dev/null "http://localhost:$PORT" && break
    sleep 0.5
  done
fi

# Streamlit draws with JavaScript after the page loads, so capture.py waits
# (WAIT seconds, default 6) before taking the picture.
"$PROJECT/venv/bin/python" "$HERE/capture.py" \
  "http://localhost:$PORT/$( { [ "$VIEW" = mission ] || [ "$VIEW" = profile ]; } && echo "$VIEW")?view=$VIEW&step=${STEP:-0}" "$OUT" "$WIDTH" "$HEIGHT" "${WAIT:-6}" > /dev/null
echo "$OUT"
