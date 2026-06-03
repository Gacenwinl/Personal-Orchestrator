#!/usr/bin/env bash
# Start Harness Web Hub if needed and open the browser.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8765}"
PIDFILE="$ROOT/artifacts/.sop_server.pid"
URL="http://127.0.0.1:${PORT}/"

if ! curl -sf "$URL/health" >/dev/null 2>&1; then
  echo "Starting Harness Web Hub on $URL"
  nohup python3 scripts/case_sop_server.py --port "$PORT" >>"$ROOT/artifacts/hub_server.log" 2>&1 &
  echo $! >"$PIDFILE"
  for _ in $(seq 1 30); do
    if curl -sf "$URL/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.2
  done
fi

if command -v open >/dev/null 2>&1; then
  open "$URL"
else
  echo "Open in browser: $URL"
fi
