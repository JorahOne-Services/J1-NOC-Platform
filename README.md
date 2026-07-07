<div align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/Wazuh-000?style=for-the-badge&logo=elasticsearch&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge">
</div>

<br>

<div align="center">
  <h1>🏢 J1 NOC Operations Platform</h1>
  <p><strong>Enterprise Network Operations Center Dashboard</strong></p>
  <p>Real-time infrastructure monitoring, SIEM integration, AI-powered assistant, and operations automation</p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-services">Services</a> •
    <a href="#-screenshots">Screenshots</a>
  </p>
</div>

---

## 📸 Screenshot

This is a CLI/backend-only tool. No screenshots available.

## ✨ Features

- **Real-Time Monitoring** — DC replication, NTP sync, DNS performance, OS images, centralized logs, helpdesk, SIEM
- **RBAC Administration** — Role-based access control with encrypted settings vault
- **AI Integration** — Ollama-powered AI assistant for operations insights
- **Wazuh SIEM** — Security information and event management integration
- **Multi-Phase Roadmap** — 14-phase development plan covering monitoring, security, networking, and AI
- **Modern Stack** — React + Vite frontend, FastAPI backend, Docker deployment
- **Auto-Install** — One-command setup for Ubuntu/Debian with systemd integration

## 🚀 Quick Start

```bash
git clone https://github.com/OneByJorah/J1-NOC-Platform.git
cd J1-NOC-Platform
cp .env.example .env
# Edit .env with your configuration
docker compose up -d
```

### One-Command Install

```bash
sudo ./setup.sh
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    J1 NOC Platform                          │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Frontend │  │ Backend  │  │ Admin    │  │ Monitoring │ │
│  │ React    │  │ FastAPI  │  │ Service  │  │ Wazuh SIEM │ │
│  │ + Vite   │  │ AsyncAPI │  │ + RBAC   │  │ Agent      │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │              │              │               │        │
│       └──────────────┼──────────────┼───────────────┘        │
│                      ▼              ▼                        │
│              ┌────────────┐  ┌────────────┐                  │
│              │ PostgreSQL │  │   Ollama   │                  │
│              │  Database  │  │  AI Engine │                  │
│              └────────────┘  └────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Services Monitored

| Service | Type | Description |
|---------|------|-------------|
| **Domain Controllers** | AD/LDAP | Replication health, authentication |
| **NTP Clients** | Time | Clock synchronization status |
| **DNS Performance** | Network | Query latency and resolution |
| **OS Images** | Deployment | Image management and deployment |
| **Centralized Logs** | System | Aggregated log collection |
| **Helpdesk** | Support | Ticket monitoring and metrics |
| **Wazuh SIEM** | Security | Event correlation and alerts |
| **Ollama AI** | LLM | AI-powered operations assistant |

## 🐳 Docker Deployment

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## 📁 Project Structure

```
J1-NOC-Platform/
├── frontend/              # React + Vite SPA
├── backend/               # FastAPI backend server
├── admin-service/         # Admin & RBAC service
├── agent/                 # Monitoring agents
├── database/              # Database migrations (Alembic)
├── monitoring/            # Wazuh SIEM integration
├── nginx/                 # Reverse proxy configuration
├── alembic/               # Database migration scripts
├── bin/                   # Utility scripts
├── scripts/               # Setup and automation
├── docs/                  # Documentation
├── .githooks/             # Git hooks
├── docker-compose.yml     # Main deployment
├── docker-compose.override.yml
└── setup.sh               # Auto-install script
```



## 🗺️ Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation & Core Dashboard | ✅ Complete |
| 2 | Overview Dashboard | ✅ Complete |
| 3 | Network Monitor | ✅ Complete |
| 4 | LDAP/AD Integration | 🔄 In Progress |
| 5 | Chrony NTP Monitoring | 🔄 In Progress |
| 6 | DNS Tools | 📋 Planned |
| 7 | PBX Integration | 📋 Planned |
| 8 | osTicket Integration | 📋 Planned |
| 9 | Notifications | 📋 Planned |
| 10 | AI Assistant | 📋 Planned |
| 11 | Security Center | 📋 Planned |
| 12 | Multi-tenant Infrastructure | 📋 Planned |
| 13 | Polish, Docs, CI | 📋 Planned |
| 14 | Initial Deployment | 📋 Planned |

## 🔒 Security

- Environment-based configuration via `.env` (never committed)
- Encrypted admin settings vault
- RBAC for multi-user access control
- Wazuh SIEM integration for security monitoring
- Regular dependency updates via Dependabot

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. This project has a 14-phase roadmap — contributions welcome on any phase.

## 📄 License

MIT © Jhonattan L. Jimenez

---

<div align="center">
  <p>🏢 Enterprise NOC, self-hosted and fully open source</p>
  <p><a href="https://github.com/OneByJorah">@OneByJorah</a></p>
</div>
