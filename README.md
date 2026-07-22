# NexusCore

Enterprise Network Operations Center (NOC) platform — unified monitoring for AD, NTP, DNS, PBX, helpdesk, and AI-powered operations.

![status](https://img.shields.io/badge/status-active-FFB300?style=flat-square)
![language](https://img.shields.io/badge/python+typescript-0d0d0c?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-FFB300?style=flat-square)

## Overview

NexusCore is a self-hosted enterprise NOC platform that provides a unified monitoring dashboard for Active Directory replication, NTP synchronization, DNS health, PBX status, helpdesk operations, and AI-powered anomaly detection. Built with FastAPI, React, Docker Compose, and OpenAI integration.

## Features

- NOC dashboard — real-time overview of all network operations
- DC replication monitoring — Active Directory health across all domain controllers
- NTP/DNS/PBX service monitoring with alerting
- Helpdesk integration — ticket metrics and status
- AI-powered anomaly detection and insights
- React frontend with responsive design
- FastAPI async backend
- Docker Compose deployment with dev/prod configs
- Alembic database migrations
- Pre-commit hooks, ruff linting, commitlint

## Architecture / Tech Stack

- **Backend**: FastAPI (Python 3.12+), Alembic
- **Frontend**: React (TypeScript)
- **AI**: OpenAI (GPT)
- **Database**: PostgreSQL
- **Monitoring**: Custom collectors for AD, NTP, DNS, PBX
- **Deployment**: Docker Compose, systemd
- **DevOps**: pre-commit, ruff, commitlint, GitHub Actions CI

## Installation

```bash
git clone https://github.com/OneByJorah/NexusCore.git
cd NexusCore

cp .env.example .env  # Configure services
docker compose up -d
```

Or local development:
```bash
./setup.sh
```

## Configuration

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for AI insights |
| `DATABASE_URL` | PostgreSQL connection string |
| `AD_DOMAIN_CONTROLLER` | DC hostname for monitoring |
| `NTP_SERVERS` | NTP servers to check |

See `.env.example` for full options.

## License

MIT — see [LICENSE](LICENSE).

---
Part of the JorahOne / J1 ecosystem — enterprise NOC for self-hosted infrastructure.
