#!/usr/bin/env bash
# J1 NOC Platform — One-command installer
# Downloads the repo, installs Docker (if missing), starts the stack,
# prompts for the first admin username/password, creates the admin,
# then prints the access URL.
#
# Run on a fresh Ubuntu/Debian server as a user with sudo:
#   curl -fsSL https://raw.githubusercontent.com/JorahOne-Services/J1-NOC-Platform/main/scripts/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/JorahOne-Services/J1-NOC-Platform.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/j1-noc-platform}"
HTTP_PORT="${HTTP_PORT:-5173}"

color() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
info() { color '0;34' "$1"; }
ok()   { color '0;32' "$1"; }
warn() { color '1;33' "$1"; }
err()  { color '0;31' "$1"; }

info '== J1 NOC Platform Installer =='

# 1. Preflight
if [[ $EUID -eq 0 ]]; then
  err 'Do not run this script as root. Run as a user with sudo access.'
  exit 1
fi

if ! command -v git &>/dev/null || ! command -v curl &>/dev/null; then
  warn 'Installing prerequisites (git, curl)...'
  sudo apt-get update -qq
  sudo apt-get install -y -qq git curl
fi

# 2. Install Docker if missing
if ! command -v docker &>/dev/null || ! command -v docker compose &>/dev/null; then
  info 'Docker not found. Installing Docker...'
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "${USER}" || true
  warn 'Docker installed. You may need to log out and back in for group changes to take effect.'
  # Try to start a new shell session in the docker group so the rest of the script works
  newgrp docker <<'NEWGRP'
    echo 'Docker group applied for this session.'
NEWGRP
fi

# Ensure we can run docker
if ! docker info &>/dev/null; then
  err 'Cannot run docker. Re-log or run: newgrp docker'
  exit 1
fi

# 3. Clone repo
if [[ -d "$INSTALL_DIR" ]]; then
  warn "Directory $INSTALL_DIR already exists. Pulling latest code..."
  cd "$INSTALL_DIR"
  git pull --ff-only
else
  info "Cloning $REPO_URL into $INSTALL_DIR..."
  sudo mkdir -p "$INSTALL_DIR"
  sudo chown "${USER}:${USER}" "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# 4. Prepare safe environment file
info 'Preparing safe .env template...'
cd "$INSTALL_DIR"
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
fi

# 5. Start stack
info 'Starting Docker stack...'
docker compose pull
docker compose up -d

# 6. Wait for backend
info 'Waiting for backend to become healthy...'
for i in {1..30}; do
  if curl -fsS "http://127.0.0.1:${HTTP_PORT}/api/setup/status" &>/dev/null; then
    break
  fi
  sleep 2
done

if ! curl -fsS "http://127.0.0.1:${HTTP_PORT}/api/setup/status" &>/dev/null; then
  err 'Backend did not become healthy. Check logs: docker logs j1-noc-platform-backend-1'
  exit 1
fi

needs_setup=$(curl -fsS "http://127.0.0.1:${HTTP_PORT}/api/setup/status" | sed -n 's/.*"needs_setup":\(true\|false\).*/\1/p')

# 7. Prompt for first admin
if [[ "$needs_setup" == "true" ]]; then
  echo
  info 'Create the first administrator account:'
  read -rp 'Admin username: ' admin_user
  while [[ -z "$admin_user" ]]; do
    err 'Username cannot be empty.'
    read -rp 'Admin username: ' admin_user
  done

  read -rsp 'Admin password: ' admin_pass
  echo
  while [[ ${#admin_pass} -lt 8 ]]; do
    err 'Password must be at least 8 characters.'
    read -rsp 'Admin password: ' admin_pass
    echo
  done

  read -rsp 'Confirm password: ' admin_pass2
  echo
  while [[ "$admin_pass" != "$admin_pass2" ]]; do
    err 'Passwords do not match.'
    read -rsp 'Admin password: ' admin_pass
    echo
    read -rsp 'Confirm password: ' admin_pass2
    echo
  done

  info 'Creating admin account...'
  curl -fsS -X POST "http://127.0.0.1:${HTTP_PORT}/api/setup" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${admin_user}\",\"password\":\"${admin_pass}\"}" >/dev/null
  ok "Admin '${admin_user}' created."
else
  info 'An admin account already exists. Skipping setup prompt.'
fi

# 8. Print access info
echo
ok 'Installation complete!'
echo
info 'Access URLs:'
echo "  Local:     http://127.0.0.1:${HTTP_PORT}"
public_ip=$(curl -fsS --max-time 3 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
if [[ -n "$public_ip" ]]; then
  echo "  Network:   http://${public_ip}:${HTTP_PORT}"
fi
echo
info 'Next steps:'
echo "  1. Open http://${public_ip:-127.0.0.1}:${HTTP_PORT}/setup (then login)"
echo "  2. Go to Admin -> Settings and enter your live credentials."
echo "  3. They are encrypted at rest in Postgres — never commit them to Git."
echo
