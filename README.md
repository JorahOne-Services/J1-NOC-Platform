<div align="center">

![NexusCore banner](docs/assets/banner.svg)

# NexusCore

Enterprise NOC platform

![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Language](https://img.shields.io/badge/language-HTML-blue)
</div>

---

<p align="center">
  <img src="docs/assets/screenshot.png" alt="NexusCore preview" width="90%">
</p>

<br>

---

## Features

- **NOC Dashboard** — Real-time overview of all network operations in a single pane.
- **AD Replication Monitoring** — Active Directory health across all domain controllers.
- **NTP/DNS/PBX Monitoring** — Service health with automated alerting and status tracking.
- **Helpdesk Integration** — Ticket metrics, SLA tracking, and status management.
- **AI-Powered Anomaly Detection** — OpenAI GPT integration for intelligent insights and predictions.
- **SNMP Discovery** — Automated network device discovery and inventory management.
- **Wazuh SIEM Integration** — Security event monitoring and compliance tracking.
- **React Frontend** — Responsive, modern dashboard with real-time updates.
- **FastAPI Backend** — Async Python 3.12+ backend with Alembic migrations.
- **Docker Compose Deployment** — One-command production deployment.

## Quick Start

```bash
git clone https://github.com/OneByJorah/NexusCore.git
cd NexusCore

cp .env.example .env  # Configure your services
docker compose up -d
```

Open **http://localhost:3000** in your browser.

### Local Development

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key for AI-powered insights |
| `DATABASE_URL` | `sqlite:///./nexuscore.db` | PostgreSQL/SQLite connection string |
| `AD_DOMAIN_CONTROLLER` | — | Domain controller hostname for monitoring |
| `NTP_SERVERS` | — | Comma-separated NTP servers to check |
| `DNS_SERVERS` | — | Comma-separated DNS servers to check |
| `PBX_HOST` | — | PBX server hostname for status monitoring |

See `.env.example` for all available options.

## Architecture

```
Browser (React) ──API──▶ FastAPI Backend ──▶ PostgreSQL
                              │
                              ├──▶ AD/LDAP Collector
                              ├──▶ NTP/DNS/PBX Monitors
                              ├──▶ OpenAI (GPT Insights)
                              └──▶ Wazuh SIEM
```

## Tech Stack

- **Backend**: FastAPI (Python 3.12+), Alembic, SQLAlchemy
- **Frontend**: React 18 (TypeScript), Vite
- **AI**: OpenAI GPT for anomaly detection and insights
- **Database**: PostgreSQL (production), SQLite (development)
- **Monitoring**: Custom collectors for AD, NTP, DNS, PBX
- **Security**: Wazuh SIEM integration, CVE scanning
- **Deployment**: Docker Compose, systemd
- **DevOps**: pre-commit, ruff linting, commitlint, GitHub Actions CI

## Project Structure

```
NexusCore/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/             # API endpoint modules
│   ├── services/            # Business logic and collectors
│   └── models/              # SQLAlchemy database models
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard pages (AI, LDAP, DNS, etc.)
│   │   └── components/      # Reusable React components
│   └── package.json
├── docker-compose.yml       # Production deployment
├── alembic/                 # Database migrations
└── .env.example             # Configuration template
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard` | GET | NOC dashboard overview |
| `/api/ad/replication` | GET | AD replication status |
| `/api/ntp/status` | GET | NTP synchronization health |
| `/api/dns/health` | GET | DNS resolution status |
| `/api/pbx/status` | GET | PBX service health |
| `/api/tickets` | GET | Helpdesk ticket metrics |
| `/api/ai/insights` | GET | AI-powered anomaly insights |

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## Security

For security concerns, see [SECURITY.md](SECURITY.md). Please report vulnerabilities to **info@jorahone.com** — do not use public issues.

## License

MIT © Jhonattan L. Jimenez

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## 🔒 Security

Found a vulnerability? Please follow our [Security Policy](SECURITY.md) and report privately to `security@jorahone.com`.

## 📄 License

[MIT License](LICENSE) © Jhonattan L. Jimenez (OneByJorah)

---

<p align="center">Built with 🌴 by <a href="https://github.com/OneByJorah">OneByJorah</a> · <a href="https://jorahone.com">jorahone.com</a></p>
