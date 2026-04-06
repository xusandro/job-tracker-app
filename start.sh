#!/bin/bash
# Starts backend (Flask) and frontend (Vite) together.
# Ctrl+C kills both.

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Backend ──────────────────────────────────────────────
(
  cd "$ROOT/backend"
  if [ ! -d ".venv" ]; then
    echo "[backend] Creating virtualenv..."
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install -r requirements.txt -q
  echo "[backend] Starting Flask on :5001"
  python app.py
) &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────
(
  cd "$ROOT/frontend"
  if [ ! -d "node_modules" ]; then
    echo "[frontend] Installing npm deps..."
    npm install
  fi
  echo "[frontend] Starting Vite dev server"
  npm run dev
) &
FRONTEND_PID=$!

# ── Shutdown handler ─────────────────────────────────────
cleanup() {
  echo ""
  echo "Stopping both servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  pkill -f "$ROOT/backend/.venv/bin/python app.py" 2>/dev/null
  echo "Done."
}
trap cleanup INT TERM

echo "Backend PID: $BACKEND_PID  |  Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both."
wait
