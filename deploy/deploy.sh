#!/bin/bash
# Called by GitHub Actions on every push to main.
# Run this on whichever EC2 needs updating after a git push.
#
# On Backend EC2:  sudo bash deploy/deploy.sh --backend
# On Frontend EC2: sudo bash deploy/deploy.sh --frontend
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="$1"

if [ -z "$MODE" ]; then
  echo "Usage: bash deploy/deploy.sh --backend | --frontend"
  exit 1
fi

echo "==> Pulling latest code..."
git -C "$ROOT" pull origin main

if [ "$MODE" = "--backend" ]; then
  echo "==> Updating backend..."
  cd "$ROOT/backend"
  .venv/bin/pip install -r requirements.txt -q
  systemctl restart gunicorn-jobtracker
  echo "==> Backend deploy complete."

elif [ "$MODE" = "--frontend" ]; then
  echo "==> Rebuilding frontend..."
  cd "$ROOT/frontend"
  npm install --silent
  npm run build
  systemctl reload nginx
  echo "==> Frontend deploy complete."

else
  echo "ERROR: Unknown mode '$MODE'. Use --backend or --frontend."
  exit 1
fi
