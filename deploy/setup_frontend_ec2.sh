#!/bin/bash
# Run once on the Frontend EC2 instance (Ubuntu).
# Installs Nginx and Node.js, builds the React app, and configures
# Nginx to serve static files and proxy /api/* to the Backend EC2.
#
# Usage:
#   sudo BACKEND_PRIVATE_IP=10.0.1.20 bash deploy/setup_frontend_ec2.sh
#
# BACKEND_PRIVATE_IP: private IP of the Backend EC2
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

: "${BACKEND_PRIVATE_IP:?BACKEND_PRIVATE_IP is required}"

echo "==> Repo root: $ROOT"
echo "==> Backend IP: $BACKEND_PRIVATE_IP"

# ── System packages ───────────────────────────────────────────────────────────
echo "==> Installing system packages..."
apt-get update -q
apt-get install -y nginx nodejs npm

# ── Build React frontend ──────────────────────────────────────────────────────
echo "==> Building React frontend..."
cd "$ROOT/frontend"
npm install --silent
npm run build

# ── Nginx config ──────────────────────────────────────────────────────────────
echo "==> Writing Nginx config..."
cat > /etc/nginx/sites-available/jobtracker <<EOF
server {
    listen 80;
    server_name _;

    root $ROOT/frontend/dist;
    index index.html;

    # Proxy API requests to the Backend EC2
    location /api/ {
        proxy_pass http://${BACKEND_PRIVATE_IP}:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # Serve React app — fallback to index.html for client-side routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

ln -sf /etc/nginx/sites-available/jobtracker /etc/nginx/sites-enabled/jobtracker
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable --now nginx
systemctl reload nginx

echo ""
echo "==> Frontend setup complete."
echo "    Public IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "    Verify: curl http://localhost"
echo "    Then open the public IP in your browser."
