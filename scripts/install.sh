#!/usr/bin/env bash
# J1 NOC Platform — Interactive Installer with Enterprise Setup
# Prompts for ALL service credentials, writes to /etc/j1-noc-platform/.env.live,
# starts the Docker stack, creates the admin user, and deploys the admin dashboard.
#
# Usage on a fresh Ubuntu/Debian server:
#   curl -fsSL https://raw.githubusercontent.com/JorahOne-Services/J1-NOC-Platform/main/scripts/install.sh | bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/JorahOne-Services/J1-NOC-Platform.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/j1-noc-platform}"
HTTP_PORT="${HTTP_PORT:-5173}"
LIVE_ENV="/etc/j1-noc-platform/.env.live"

# ─── UI Helpers ───
color()  { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
info()   { color '0;34' "  ℹ️  $1"; }
ok()     { color '0;32' "  ✅ $1"; }
warn()   { color '1;33' "  ⚠️  $1"; }
err()    { color '0;31' "  ❌ $1"; }
header() { echo; color '1;36' "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; color '1;36' "   $1"; color '1;36' "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }

prompt_optional() {
  local label="$1" var="$2" default="${3:-}"
  read -rp "  $label [$default]: " val
  eval "$var='${val:-$default}'"
}
prompt_secret() {
  local label="$1" var="$2"
  local val val2
  while true; do
    read -rsp "  $label: " val; echo
    if [[ -z "$val" ]]; then
      warn "Value cannot be empty"; continue
    fi
    read -rsp "  Confirm: " val2; echo
    [[ "$val" == "$val2" ]] && break
    err "Passwords do not match. Try again."
  done
  eval "$var='$val'"
}
prompt_yesno() {
  local label="$1" var="$2" default="${3:-y}"
  read -rp "  $label [${default}]: " val
  case "${val:-$default}" in y|Y|yes|YES) eval "$var=true" ;; *) eval "$var=false" ;; esac
}
prompt_toggle() {
  local label="$1" var="$2"
  read -rp "  $label [y/N]: " val
  case "${val:-N}" in y|Y|yes) eval "$var=true" ;; *) eval "$var=false" ;; esac
}

# ─── 1. Preflight ───
header "Preflight Checks"
if [[ $EUID -eq 0 ]]; then
  err "Do NOT run as root. Run as a user with sudo."
  exit 1
fi
ok "User: $(whoami)"

for cmd in git curl; do
  if ! command -v $cmd &>/dev/null; then
    info "Installing $cmd..."
    sudo apt-get update -qq && sudo apt-get install -y -qq $cmd
  fi
done
ok "Prerequisites ready"

# ─── 2. Install Docker ───
header "Docker Installation"
if ! command -v docker &>/dev/null; then
  info "Docker not found. Installing..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "${USER}" || true
  warn "Docker installed. You may need to log out and back in for group changes."
else
  ok "Docker already installed ($(docker --version 2>/dev/null))"
fi

if ! docker info &>/dev/null; then
  err "Cannot run docker. Re-log or run: newgrp docker"
  exit 1
fi
if ! docker compose version &>/dev/null; then
  info "Installing Docker Compose plugin..."
  sudo apt-get install -y -qq docker-compose-plugin
fi
ok "Docker Compose ready"

# ─── 3. Clone / Update Repo ───
header "Repository Setup"
if [[ -d "$INSTALL_DIR" ]]; then
  info "Directory exists. Pulling latest..."
  cd "$INSTALL_DIR"
  git pull --ff-only
else
  info "Cloning repository..."
  sudo mkdir -p "$INSTALL_DIR"
  sudo chown "${USER}:${USER}" "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi
ok "Repo ready at $INSTALL_DIR"

# ─── 4. Interactive Credential Collection ───
header "🔐  Service Credentials"
echo "  Enter credentials for each service. Leave blank to use defaults."
echo

declare -A CREDS

# Database
header "PostgreSQL Database"
prompt_optional "Username"    CREDS[POSTGRES_USER]    "jnop"
prompt_secret  "Password"    CREDS[POSTGRES_PASSWORD]
prompt_optional "Database"   CREDS[POSTGRES_DB]      "jnop"

# Redis
header "Redis Cache"
prompt_secret  "Redis Password" CREDS[REDIS_PASSWORD]

# Security
header "Application Security"
prompt_secret  "Secret Key (64+ chars, random)" CREDS[SECRET_KEY]
CREDS[SECRET_KEY]=${CREDS[SECRET_KEY]:-$(openssl rand -hex 32)}
BACKEND_CORS="http://localhost:${HTTP_PORT},http://127.0.0.1:${HTTP_PORT}"
CREDS[BACKEND_CORS_ORIGINS]="$BACKEND_CORS"
ok "CORS origins: $BACKEND_CORS"

# Monitoring
header "Monitoring"
prompt_secret  "Grafana Admin Password" CREDS[GRAFANA_ADMIN_PASSWORD]

# Telephony (SNMP)
header "Telephony / Mitel SNMP"
prompt_optional "Mitel SNMP Host"      CREDS[MITEL_SNMP_HOST]     "localhost"
prompt_optional "Mitel SNMP Community" CREDS[MITEL_SNMP_COMMUNITY] "public"

# Helpdesk
header "Helpdesk Integrations"
prompt_toggle "Configure osTicket?" OSTICKET_ENABLE
if [[ "$OSTICKET_ENABLE" == "true" ]]; then
  prompt_optional "osTicket URL"    CREDS[OSTICKET_BASE_URL] "http://localhost:8082"
  prompt_secret  "osTicket API Key" CREDS[OSTICKET_API_KEY]
fi

prompt_toggle "Configure LDAP / Active Directory?" LDAP_ENABLE
if [[ "$LDAP_ENABLE" == "true" ]]; then
  prompt_optional "LDAP URL"        CREDS[LDAP_URL]        "ldap://localhost:389"
  prompt_optional "LDAP Domain"     CREDS[LDAP_DOMAIN]     "example.local"
  prompt_optional "LDAP Bind DN"    CREDS[LDAP_BIND_DN]    "cn=admin,dc=example,dc=local"
  prompt_secret  "LDAP Bind Password" CREDS[LDAP_BIND_PASSWORD]
fi

prompt_toggle "Configure Wazuh SIEM?" WAZUH_ENABLE
if [[ "$WAZUH_ENABLE" == "true" ]]; then
  prompt_optional "Wazuh API URL"  CREDS[WAZUH_API_URL] "https://localhost:55000"
  prompt_optional "Wazuh Username" CREDS[WAZUH_USERNAME] "wazuh"
  prompt_secret  "Wazuh Password"  CREDS[WAZUH_PASSWORD]
fi

# Notifications
header "Notification Channels"
prompt_toggle "Configure Telegram Bot?" TG_ENABLE
if [[ "$TG_ENABLE" == "true" ]]; then
  prompt_secret "Telegram Bot Token" CREDS[TELEGRAM_BOT_TOKEN]
fi

prompt_toggle "Configure Microsoft Teams?" TEAMS_ENABLE
if [[ "$TEAMS_ENABLE" == "true" ]]; then
  prompt_optional "Teams Webhook URL" CREDS[TEAMS_WEBHOOK] "https://outlook.office.com/webhook/..."
fi

prompt_toggle "Configure SMTP Email?" SMTP_ENABLE
if [[ "$SMTP_ENABLE" == "true" ]]; then
  prompt_optional "SMTP Host"     CREDS[NOTIFY_SMTP_HOST]     "smtp.example.com"
  prompt_optional "SMTP Username" CREDS[NOTIFY_SMTP_USER]     "notify@example.com"
  prompt_secret  "SMTP Password"  CREDS[NOTIFY_SMTP_PASSWORD]
fi

# ─── 5. Write Live Environment File ───
header "Writing Live Credentials"
sudo mkdir -p "$(dirname "$LIVE_ENV")"
cat << 'LIVEEOF' | sudo tee "$LIVE_ENV" > /dev/null
# J1 NOC Platform — Live Credentials
# Generated by interactive installer
# Permissions: 600 (root only)
LIVEEOF

# Append each credential
for key in "${!CREDS[@]}"; do
  val="${CREDS[$key]}"
  # Shell-safe quoting
  val="${val//\'/\\\'}"
  echo "$key='$val'" | sudo tee -a "$LIVE_ENV" > /dev/null
done
sudo chmod 600 "$LIVE_ENV"
sudo chown root:root "$LIVE_ENV"
ok "Credentials written to $LIVE_ENV (root:root, 600)"

# ─── 6. Prepare .env for Docker Compose ───
header "Starting Stack"
cp "$LIVE_ENV" "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"

# ─── 7. Build and Start Stack ───
info "Building images and starting containers..."
cd "$INSTALL_DIR"
docker compose build admin-service 2>&1 | tail -1 || true
docker compose pull 2>&1 | tail -3
docker compose up -d 2>&1 | head -10

# ─── 8. Wait for Backend ───
info "Waiting for backend and admin service to become healthy..."
for i in {1..45}; do
  backend_ok=false
  admin_ok=false
  if curl -fsS "http://127.0.0.1:${HTTP_PORT}/healthz" &>/dev/null; then backend_ok=true; fi
  if curl -fsS "http://127.0.0.1:${HTTP_PORT}/api/health" &>/dev/null; then admin_ok=true; fi
  $backend_ok && $admin_ok && break
  sleep 2
done

if ! curl -fsS "http://127.0.0.1:${HTTP_PORT}/healthz" &>/dev/null; then
  warn "Backend not yet healthy. Check logs: docker compose logs backend"
fi

# ─── 9. Deploy Admin Dashboard to Volume ───
info "Deploying admin dashboard..."
ADMIN_HTML_SRC="$INSTALL_DIR/frontend/admin.html"
ADMIN_VOLUME="/var/lib/docker/volumes/jnop_frontend_dist/_data"
if [[ -d "$ADMIN_VOLUME" ]]; then
  sudo mkdir -p "$ADMIN_VOLUME/admin"
  sudo cp "$ADMIN_HTML_SRC" "$ADMIN_VOLUME/admin/index.html"
  sudo chown -R 1000:1000 "$ADMIN_VOLUME/admin" 2>/dev/null || true
  ok "Admin dashboard deployed to $ADMIN_VOLUME/admin/index.html"
else
  warn "Frontend volume not found — admin dashboard will be deployed on next restart"
fi

# ─── 10. Create Admin User ───
header "👤  Create Administrator"
echo "  You need at least one admin account to log in."
echo

ADMIN_USER=""
ADMIN_PASS=""
read -rp "  Admin username [admin]: " ADMIN_USER
ADMIN_USER="${ADMIN_USER:-admin}"

while true; do
  read -rsp "  Admin password (8+ chars): " ADMIN_PASS; echo
  if [[ ${#ADMIN_PASS} -ge 8 ]]; then break; fi
  err "Password must be at least 8 characters."
done
read -rsp "  Confirm password: " ADMIN_PASS2; echo
if [[ "$ADMIN_PASS" != "$ADMIN_PASS2" ]]; then
  err "Passwords do not match. Run again after setup."
else
  info "Creating admin account..."
  curl -fsS -X POST "http://127.0.0.1:${HTTP_PORT}/api/admin/setup/bootstrap" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}" 2>/dev/null && \
  curl -fsS -X POST "http://127.0.0.1:${HTTP_PORT}/api/admin/setup/complete" \
    -H 'Content-Type: application/json' \
    -d "{\"password\":\"${ADMIN_PASS}\"}" 2>/dev/null && \
  ok "Admin '${ADMIN_USER}' created." || warn "Admin creation had issues — try the setup wizard."
fi

# ─── 11. Restore Safe .env Template ───
header "Finalizing"
if [[ -f "$INSTALL_DIR/.env.example" ]]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  chmod 644 "$INSTALL_DIR/.env"
  ok "Repo .env restored to safe template"
else
  warn "No .env.example found — keeping live .env (DO NOT COMMIT)"
fi

# ─── 12. Print Summary ───
header "🎉  Installation Complete!"
echo
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │                                                 │"
echo "  │   🛡️  J1 NOC Platform — Enterprise Edition     │"
echo "  │                                                 │"
echo "  │   Dashboard:     http://<your-server-ip>:${HTTP_PORT}   │"
echo "  │   Admin Panel:   http://<your-server-ip>:${HTTP_PORT}/admin/  │"
echo "  │   Grafana:       http://<your-server-ip>:3000        │"
echo "  │                                                 │"
echo "  │   Username:  ${ADMIN_USER:-admin}                       │"
echo "  │   Password:  <as entered>                       │"
echo "  │                                                 │"
echo "  └─────────────────────────────────────────────────┘"
echo
echo "  📋  Next Steps:"
echo "    1. Open http://<your-server-ip>:${HTTP_PORT} — main dashboard"
echo "    2. Open http://<your-server-ip>:${HTTP_PORT}/admin/ — admin panel"
echo "    3. Configure integrations in Admin → Integrations"
echo "    4. Enter credentials in Admin → Credentials"
echo "    5. Run deploy after changes: sudo ./scripts/deploy.sh"
echo
echo "  🔒  Live credentials are stored in:"
echo "     $LIVE_ENV (root:600)"
echo