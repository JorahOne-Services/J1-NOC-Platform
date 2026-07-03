# J1 NOC Platform — Live Deployment Guide

## Where live secrets live
Production secrets are stored in `/etc/j1-noc-platform/.env.live` with mode `600`, owned by root. The repo itself never contains live credentials.

## How to update the live server
1. Edit code in `/home/j1admin/J1-NOC-Platform` as normal.
2. Commit and push to GitHub.
3. Run the deploy script as root:
   ```bash
   sudo /home/j1admin/J1-NOC-Platform/scripts/deploy.sh
   ```
The script:
- Pulls latest code
- Copies `/etc/j1-noc-platform/.env.live` into the project
- Runs `docker compose up -d --build --remove-orphans`
- Resets the repo `.env` to `.env.example` so no secrets remain in the working tree

## How to start/stop the live service via systemd
```bash
sudo cp /home/j1admin/J1-NOC-Platform/systemd/j1-noc-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now j1-noc-platform
```

## Pre-commit hook (secret guard)
Install once per clone:
```bash
cp /home/j1admin/J1-NOC-Platform/.githooks/pre-commit /home/j1admin/J1-NOC-Platform/.git/hooks/pre-commit
chmod +x /home/j1admin/J1-NOC-Platform/.git/hooks/pre-commit
```
This blocks commits that look like they contain passwords, API keys, tokens, or private keys.

## Updating live secrets
Edit `/etc/j1-noc-platform/.env.live` directly on the server. Then re-run the deploy script.

## Important rules
- Never commit `.env`, `.env.live`, `*.pem`, `*.key`, or `*.crt`.
- The repo `.env` should always match `.env.example` (template values only).
- All real credentials must live in `/etc/j1-noc-platform/.env.live`.
