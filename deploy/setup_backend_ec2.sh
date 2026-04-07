#!/bin/bash
# Run once on the Backend EC2 instance (Ubuntu).
# Installs Python, Gunicorn, and sets up the Flask app as a systemd service.
# No Nginx needed — backend is only accessed internally from the Frontend EC2.
#
# Usage:
#   sudo bash deploy/setup_backend_ec2.sh
#
# Before running, make sure .env exists at the repo root with:
#   DB_HOST=<DB EC2 private IP>
#   DB_USER=jobtracker
#   DB_PASSWORD=<your db password>
#   DB_NAME=job_tracker
#   SECRET_KEY=<random secret>
#   FRONTEND_ORIGIN=http://<FRONTEND EC2 public IP>
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Repo root: $ROOT"

if [ ! -f "$ROOT/.env" ]; then
  echo "ERROR: .env file not found at $ROOT/.env"
  echo "Create it before running this script."
  exit 1
fi

# ── System packages ───────────────────────────────────────────────────────────
echo "==> Installing system packages..."
apt-get update -q
apt-get install -y python3-venv python3-pip

# ── Python venv + deps ────────────────────────────────────────────────────────
echo "==> Setting up Python virtualenv..."
cd "$ROOT/backend"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install gunicorn -q
.venv/bin/pip install -r requirements.txt -q

# ── Gunicorn systemd service ──────────────────────────────────────────────────
echo "==> Writing systemd service..."
cat > /etc/systemd/system/gunicorn-jobtracker.service <<EOF
[Unit]
Description=Gunicorn for Job Tracker Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$ROOT/backend
ExecStart=$ROOT/backend/.venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 app:app
Restart=always
EnvironmentFile=$ROOT/.env

[Install]
WantedBy=multi-user.target
EOF

# ── Start service ─────────────────────────────────────────────────────────────
echo "==> Starting Gunicorn service..."
systemctl daemon-reload
systemctl enable --now gunicorn-jobtracker

echo ""
echo "==> Backend setup complete."
echo "    Flask API is running on port 5001."
echo "    Private IP: $(hostname -I | awk '{print $1}')"
echo ""
echo "    Verify: curl http://localhost:5001/api/health"
