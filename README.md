<div align="center">

  <img src="https://raw.githubusercontent.com/OneByJorah/NexusCore/main/docs/logo.png" alt="NexusCore Logo" width="120">

  # NexusCore

  **Enterprise Network Operations Center (NOC) Platform**

  Unified monitoring dashboard for Active Directory, NTP, DNS, PBX, helpdesk, and AI-powered operations assistance.

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://react.dev/)
  [![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
  [![CI](https://github.com/OneByJorah/NexusCore/actions/workflows/ci.yml/badge.svg)](https://github.com/OneByJorah/NexusCore/actions/workflows/ci.yml)
  [![AI-Powered](https://img.shields.io/badge/AI-Powered-9B59B6?style=flat&logo=openai&logoColor=white)](https://openai.com/)

  [Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Services](#services) • [Contributing](#contributing)

</div>

---

## Screenshots

<div align="center">

| NOC Dashboard | Service Monitor | AI Insights |
|---------------|-----------------|-------------|
| ![NOC Dashboard](docs/screenshots/noc-dashboard.png) | ![Service Monitor](docs/screenshots/service-monitor.png) | ![AI Insights](docs/screenshots/ai-insights.png) |

</div>

> **Tip:** NexusCore provides real-time monitoring of all critical network services with AI-powered anomaly detection.

---

## Features

| Feature | Description |
|---------|-------------|
| **NOC Dashboard** | Real-time overview of all network operations |
| **DC Replication** | Active Directory replication monitoring |
| **NTP Monitoring** | Chrony/NTP server health and sync status |
| **DNS Management** | BIND/Unbound DNS server monitoring |
| **PBX Integration** | Asterisk/FreePBX voice system status |
| **Helpdesk Integration** | osTicket/OStiCK ticket tracking |
| **AI Monitoring** | Machine learning anomaly detection |
| **Windows Agent** | Server monitoring agent for Windows endpoints |
| **Docker Deploy** | One-command deployment via Docker Compose |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Network access to monitored services

### Installation

```bash
# Clone the repository
git clone https://github.com/OneByJorah/NexusCore.git
cd NexusCore

# Copy the example environment
cp .env.example .env

# Start the platform
docker compose up -d
```

### Access the Dashboard

Open **http://localhost:5173** in your browser.

### First-Time Setup

1. Visit `/setup` and create the first administrator account.
2. Go to **Admin > Settings** and enter credentials for your infrastructure services.
3. Credentials are encrypted at rest in PostgreSQL — never commit them to Git.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NexusCore                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐      ┌──────────┐      ┌──────────────────────┐    │
│  │ Browser  │ ───▶ │  Nginx   │ ───▶ │    FastAPI Backend   │    │
│  └──────────┘      └──────────┘      └──────────┬──────────┘    │
│                                                  │              │
│  ┌───────────────────────────────────────────────┼───────────┐ │
│  │              Service Connectors               │           │ │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐          │ │
│  │  │ AD  │  │ NTP │  │ DNS │  │ PBX │  │Help │          │ │
│  │  │ Rep │  │Mon  │  │Mon  │  │Mon  │  │desk │          │ │
│  │  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  AI Engine                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│  │  │ Anomaly  │  │Predictive│  │ Alert    │              │ │
│  │  │Detection │  │Analysis  │  │ Routing  │              │ │
│  │  └──────────┘  └──────────┘  └──────────┘              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| **Frontend** | React 18, TypeScript, Vite |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI/ML** | Ollama, OpenAI-compatible providers |
| **Windows Agent** | Python, psutil, httpx |
| **Observability** | Prometheus, Loki, Grafana |
| **Deployment** | Docker Compose |

---

## Environment Variables

All runtime configuration is loaded via environment variables. Copy `.env.example` to `.env` and customize.

| Variable | Default | Description |
|----------|---------|-------------|
| `NOC_URL` | `http://127.0.0.1:8000` | NOC backend URL used by external agents and scripts |
| `SECRET_KEY` | `change-me` | Application secret key (change in production) |
| `DATABASE_URL` | `postgresql://jnop:change-me@postgres:5432/jnop` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379` | Redis connection string |
| `POSTGRES_USER` | `jnop` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `change-me` | PostgreSQL password |
| `POSTGRES_DB` | `jnop` | PostgreSQL database name |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |
| `GRAFANA_ADMIN_PASSWORD` | `change-me` | Grafana admin password |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LDAP_URL` | `ldap://localhost:389` | Active Directory / LDAP server |
| `MITEL_SNMP_HOST` | `localhost` | Mitel PBX SNMP host |
| `OSTICKET_URL` | `http://localhost:8082` | osTicket base URL |
| `TELEGRAM_BOT_TOKEN` | `change-me` | Telegram bot token for notifications |

---

## Windows Agent

The Python-based Windows agent pushes services, event logs, and custom logs to the NOC backend.

```powershell
# Configure the agent via environment variables
$env:NOC_URL = "http://127.0.0.1:8000"
$env:AGENT_TOKEN = "change-me"

cd agent/windows_agent
pip install -r requirements.txt
python main.py
```

The agent defaults to `http://127.0.0.1:8000` when `NOC_URL` is not set.

---

## Services

### Active Directory Replication

```bash
curl http://localhost:8000/api/ad/replication
curl http://localhost:8000/api/ad/partners
```

### NTP Monitoring

```bash
curl http://localhost:8000/api/ntp/status
curl http://localhost:8000/api/ntp/servers
```

### DNS Monitoring

```bash
curl http://localhost:8000/api/dns/health
curl http://localhost:8000/api/dns/zones
```

### PBX Integration

```bash
curl http://localhost:8000/api/pbx/status
curl http://localhost:8000/api/pbx/calls
```

---

## Development

### Local Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Local Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Lint & Test

```bash
# Backend
cd backend
ruff check .
ruff format --check .
pytest

# Frontend
cd frontend
pnpm build
```

---

## Deployment

For production deployments, see [docs/LIVE_DEPLOYMENT.md](docs/LIVE_DEPLOYMENT.md).

```bash
# Quick start (development)
cp .env.example .env
docker compose up -d
```

---

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

Copyright © Jhonattan L. Jimenez.

---

## Security

For security concerns, see [SECURITY.md](SECURITY.md). Please report vulnerabilities to **info@jorahone.com** — do not use public issues.

---

## Support

- Email: info@jorahone.com
- Issues: [GitHub Issues](https://github.com/OneByJorah/NexusCore/issues)
- Documentation: [docs/](docs/)

---

<div align="center">

  **Built by [Jhonattan L. Jimenez](https://github.com/OneByJorah)**

  [Back to Top](#nexuscore)

</div>
