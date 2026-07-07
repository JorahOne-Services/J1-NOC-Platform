#!/usr/bin/env bash
# J1 NOC Platform deploy script for live/production server
# Live secrets are loaded from /etc/j1-noc-platform/.env.live (mode 600)
# The repository .env is restored to a safe template after deployment.
set -euo pipefail

PROJECT_DIR="/home/j1admin/J1-NOC-Platform"
LIVE_ENV="/etc/j1-noc-platform/.env.live"
EXAMPLE_ENV="$PROJECT_DIR/.env.example"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

if [[ $EUID -ne 0 ]]; then
  log "ERROR: must be run as root (uses systemctl)"
  exit 1
fi

if [[ ! -f "$LIVE_ENV" ]]; then
  log "ERROR: live env not found at $LIVE_ENV"
  exit 1
fi

cd "$PROJECT_DIR"

log "Pulling latest code..."
sudo -u j1admin git pull origin main

log "Loading live environment..."
cp "$LIVE_ENV" "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"

log "Deploying containers..."
docker compose up -d --build --remove-orphans

log "Applying database migrations (Alembic)..."
docker compose exec -T backend alembic upgrade head || log "WARNING: alembic upgrade failed — check logs"

log "Waiting for backend health..."
sleep 20
if ! docker ps | grep -q "jnop-backend.*healthy"; then
  log "WARNING: backend not healthy yet — check docker logs jnop-backend"
fi

log "Deploying admin dashboard to nginx volume..."
ADMIN_SRC="$PROJECT_DIR/frontend/admin.html"
ADMIN_DST="/var/lib/docker/volumes/jnop_frontend_dist/_data/admin"
if [[ -f "$ADMIN_SRC" ]] && [[ -d "$(dirname "$ADMIN_DST")" ]]; then
  mkdir -p "$ADMIN_DST"
  cp "$ADMIN_SRC" "$ADMIN_DST/index.html"
  chown -R 1000:1000 "$ADMIN_DST" 2>/dev/null || true
  log "Admin dashboard deployed to $ADMIN_DST/index.html"
else
  log "WARNING: admin template or volume not found — skipping admin deploy"
fi

log "Resetting repo .env to safe template..."
cp "$EXAMPLE_ENV" "$PROJECT_DIR/.env"
chmod 644 "$PROJECT_DIR/.env"

log "Verifying no live secrets remain in working tree..."
if git status --short | grep -E "\.env$"; then
  log "ERROR: .env is still tracked/modified — review manually"
  exit 1
fi

log "Deploy complete."
