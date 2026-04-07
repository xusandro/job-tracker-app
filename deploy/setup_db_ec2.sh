#!/bin/bash
# Run once on the DB EC2 instance (Ubuntu).
# Sets up MySQL, creates the job_tracker database and app user.
#
# Usage:
#   sudo bash deploy/setup_db_ec2.sh
#
# Before running, set:
#   MYSQL_ROOT_PASSWORD  - password for MySQL root user
#   APP_DB_PASSWORD      - password for the app DB user
#   BACKEND_PRIVATE_IP   - private IP of the Backend EC2 (e.g. 10.0.1.20)
#
# Example:
#   sudo MYSQL_ROOT_PASSWORD=rootpass APP_DB_PASSWORD=apppass \
#        BACKEND_PRIVATE_IP=10.0.1.20 bash deploy/setup_db_ec2.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD is required}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"
: "${BACKEND_PRIVATE_IP:?BACKEND_PRIVATE_IP is required}"

APP_DB_USER="jobtracker"
APP_DB_NAME="job_tracker"

# ── Install MySQL ─────────────────────────────────────────────────────────────
echo "==> Installing MySQL..."
apt-get update -q
apt-get install -y mysql-server

# ── Secure and configure MySQL ────────────────────────────────────────────────
echo "==> Configuring MySQL..."

# Set root password and secure installation
mysql --user=root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
SQL

# ── Create database and app user ──────────────────────────────────────────────
echo "==> Creating database and user..."
mysql --user=root --password="${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS ${APP_DB_NAME};
CREATE USER IF NOT EXISTS '${APP_DB_USER}'@'${BACKEND_PRIVATE_IP}' IDENTIFIED BY '${APP_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${APP_DB_NAME}.* TO '${APP_DB_USER}'@'${BACKEND_PRIVATE_IP}';
FLUSH PRIVILEGES;
SQL

# ── Run schema ────────────────────────────────────────────────────────────────
echo "==> Running schema..."
mysql --user=root --password="${MYSQL_ROOT_PASSWORD}" ${APP_DB_NAME} < "$ROOT/database/schema.sql"

# ── Allow remote connections from backend EC2 ─────────────────────────────────
echo "==> Configuring MySQL to accept remote connections..."
MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
sed -i "s/^bind-address\s*=.*/bind-address = 0.0.0.0/" "$MYSQL_CONF"

systemctl restart mysql

echo ""
echo "==> DB setup complete."
echo "    Host: $(hostname -I | awk '{print $1}')"
echo "    Database: ${APP_DB_NAME}"
echo "    App user: ${APP_DB_USER}@${BACKEND_PRIVATE_IP}"
echo ""
echo "    Use these values in your backend .env:"
echo "    DB_HOST=<this EC2 private IP>"
echo "    DB_USER=${APP_DB_USER}"
echo "    DB_PASSWORD=${APP_DB_PASSWORD}"
echo "    DB_NAME=${APP_DB_NAME}"
