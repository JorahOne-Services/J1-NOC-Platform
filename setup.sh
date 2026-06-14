#!/usr/bin/env bash
set -euo pipefail
# Simple bootstrap for testing/live switch.
if [ ! -f .env ]; then
  cp .env.example .env
fi
echo "Edit .env and replace placeholders with live credentials, then run: docker compose up -d"
