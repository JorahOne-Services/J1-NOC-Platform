# INTENT.md — J1-PIPELINE Phase -1 (ORACLE)

**Repository:** `OneByJorah/J1-NOC-Platform`
**Analysis Date:** 2026-07-05
**Analyst:** J1-PIPELINE ORACLE (read-only)
**Status:** Intent Reconstructed

---

## What This System Does

### Technical Role

J1 NOC Platform is a self-hosted, enterprise-grade **Network Operations Center (NOC) dashboard** that provides real-time infrastructure monitoring, SIEM integration, AI-powered operations assistance, and IT automation in a single web application. It is deployed via Docker Compose and designed to run on-premises or on a single Ubuntu/Debian server.

| Category | Services | Ports |
|----------|----------|-------|
| **Web Layer** | nginx (reverse proxy), Frontend (React + Vite SPA) | 80/443 (nginx), 5173 (dev) |
| **API Layer** | Backend (FastAPI v11.0.0), Admin Service (FastAPI v1.0.0) | 8000 (backend), 8081 (admin) |
| **Data Layer** | PostgreSQL 16, Redis 7.4 (with AOF persistence) | 5432, 6379 |
| **Monitoring** | Prometheus, Grafana 11.4, Loki 3.2, SNMP Exporter | 9090, 3000, 3100 |
| **Security** | CrowdSec v1.7.8, Wazuh SIEM integration | — |
| **AI** | Ollama (local LLM) integration | 11434 |

**Monitored infrastructure domains:**
- **Domain Controllers** — AD/LDAP replication health and authentication
- **NTP/Chrony** — Clock synchronization status and drift
- **DNS** — Query latency and resolution performance
- **OS Images** — Image management and deployment
- **Centralized Logs** — Aggregated log collection (Loki)
- **Helpdesk** — osTicket ticket monitoring and metrics
- **Wazuh SIEM** — Security event correlation and alerts
- **Mitel PBX** — SNMP-based phone system health (CPU, memory, disk, active calls, trunks)
- **SSL Certificates** — Certificate expiry monitoring with 90-day uptime heatmaps
- **Windows Agents** — Remote Windows service/event/log collection via Python agent

### Operational Role

The system is consumed by **NOC operators and IT administrators** who need a single-pane-of-glass view across their entire infrastructure. It replaces the need to log into separate tools for:
- AD health checks
- NTP synchronization monitoring
- DNS performance benchmarking
- PBX/telephony health
- Helpdesk ticket tracking
- SIEM alert triage
- SSL certificate lifecycle management
- Log aggregation and search

The platform provides an **onboarding wizard** for first-run setup, **RBAC** for multi-user access, an **encrypted settings vault** (Fernet-encrypted in PostgreSQL) for storing live credentials, and a **notification system** supporting Telegram, Teams, Email, Slack, and PagerDuty.

---

## Why This Was Built

### Real Problem

Small-to-medium IT teams and managed service providers (MSPs) operating NOCs need a unified dashboard to monitor heterogeneous infrastructure — Active Directory, NTP, DNS, PBX, helpdesk, SIEM, and SSL certificates — but lack the budget or headcount for enterprise tools like SolarWinds, ServiceNow, or Splunk. Each monitoring domain requires its own tool, its own login, and its own training. The operational pain is context-switching between 6-10 different UIs to answer a single question like "what's the current state of the network?"

### Why Existing Tools Were Insufficient

- **SolarWinds / PRTG / Zabbix** — Powerful but expensive, complex to configure, and require dedicated Windows servers. Overkill for a lean NOC team.
- **Grafana + Prometheus stack alone** — Excellent for metrics but lacks SIEM integration, helpdesk ticketing, PBX monitoring, and a purpose-built NOC UI. Requires significant custom development to get a unified dashboard.
- **Wazuh standalone** — Great SIEM but no infrastructure monitoring dashboard, no helpdesk integration, no AI assistant.
- **osTicket standalone** — Helpdesk only, no infrastructure visibility.
- **Commercial NOC-as-a-Service** — Monthly per-device costs that scale poorly for growing infrastructure.
- **Existing open-source NOC tools (LibreNMS, Observium, Checkmk)** — Focused on SNMP/network device monitoring but lack AD, PBX, helpdesk, SIEM, and AI integration in a single package.

No single open-source tool combined **infrastructure monitoring + SIEM + helpdesk + AI assistant + PBX monitoring + SSL management** in a self-hosted, Docker-deployable package with a modern React UI.

### What Triggered Development

The JorahOne organization (OneByJorah / JorahOne LLC) needed an internal NOC platform to monitor its own infrastructure — domain controllers, NTP, DNS, PBX, and security events — and wanted a single, self-hosted, open-source solution that could be deployed with one command. The development was triggered by the operational need to consolidate multiple monitoring tools into a unified dashboard, and the broader JorahOne ecosystem's emphasis on self-hosted, AI-augmented infrastructure management.

The initial commit ("Add files via upload") was a bulk import of a pre-built codebase, suggesting the project was developed externally or in a private repository before being published under the OneByJorah organization.

### Ecosystem Fit

```
JorahOne / OneByJorah Ecosystem
├── J1-NOC-Platform          ← Enterprise NOC dashboard (this repo)
├── J1-Agent (implied)       ← Windows monitoring agent (agent/ subdirectory)
├── Hermes Agent             ← AI agent platform (separate repo, referenced in software-development/)
└── Other J1 repos            ← Supporting infrastructure tools
```

The NOC platform is the **operational visibility layer** for JorahOne's infrastructure. It integrates with:
- **Wazuh** for SIEM (external dependency)
- **Ollama** for local AI (external dependency)
- **osTicket** for helpdesk (external dependency)
- **Mitel PBX** via SNMP (external dependency)
- **Prometheus + Grafana + Loki** for metrics and logs (bundled in Docker Compose)
- **CrowdSec** for intrusion prevention (bundled in Docker Compose)

---

## Operational Classification

**Classification: BETA**

Evidence:
- **Version labels**: Backend v11.0.0, Admin Service v1.0.0, Windows Agent v1.0.0 — versioning is inconsistent and suggests rapid iteration rather than stable releases
- **Health checks**: Every Docker service has health checks configured (nginx, backend, frontend, postgres, redis, prometheus, grafana, loki)
- **CI/CD**: GitHub Actions CI (Python compile check + frontend build), CodeQL scanning (Python, JS, TS), Dependabot (pip, npm, docker, GitHub Actions)
- **Security posture**: Encrypted settings vault (Fernet), RBAC, pre-commit secret guard hooks, CodeQL scanning, SECURITY.md (template only — not populated with real version support info)
- **Monitoring**: Prometheus, Grafana, Loki, CrowdSec bundled; SNMP exporter configured
- **Backup**: PostgreSQL volume with named Docker volumes; no explicit backup strategy documented
- **Live deployment**: systemd service file, deploy script with secret isolation, live deployment guide documented
- **Community readiness**: CODE_OF_CONDUCT.md (full), CONTRIBUTING.md (minimal), LICENSE (MIT), issue/PR templates, bug report + feature request templates
- **Testing**: Minimal — 2 test files (test_auth.py, test_dashboard.py) with basic health/login/dashboard tests; no test runner configured in CI (only `py_compile` check)
- **Roadmap**: 14-phase plan; phases 1-3 complete, 4-5 in progress, 6-14 planned — significant functionality still under development
- **Documentation**: Comprehensive README, live deployment guide, deployment plan/report, roadmap, screenshots directory
- **Naming discrepancy**: README brand is "J1 NOC Operations Platform" / "JNOP"; repo name is "J1-NOC-Platform"; internal Docker volume prefix is `jnop_`

---

## Key Architectural Decisions

1. **Docker Compose as the sole deployment model** — All services run in containers with named volumes and internal/public network isolation. No Kubernetes, no swarm. This simplifies deployment to a single server and aligns with the "one-command install" goal.

2. **Dual-database architecture** — The main backend uses PostgreSQL (via SQLAlchemy) for persistent data (users, roles, customers, sites, agents, events, settings). The admin-service uses SQLite for its own admin/onboarding data. This creates a split where admin operations (login, onboarding, tab management) go through a separate FastAPI service with a simpler schema, while the main backend handles monitoring data.

3. **Encrypted settings vault** — Live credentials (API keys, passwords, SNMP communities) are stored Fernet-encrypted in PostgreSQL rather than in environment variables or plaintext config files. This allows runtime credential management through the admin UI without redeploying containers.

4. **Secret isolation for production** — Live secrets live in `/etc/j1-noc-platform/.env.live` (mode 600, root-owned). The deploy script copies them in, runs `docker compose up -d --build`, then scrubs the working tree `.env` back to the example template. The systemd service does the same on start/stop. This prevents credential leaks from git history.

5. **Windows Agent as a separate Python service** — Rather than using Wazuh agents or Telegraf for Windows monitoring, the project ships a custom Python agent (PyInstaller-packaged) that collects Windows services, event logs (System/Application/Security), and custom log files (e.g., Google CloudSync logs) and pushes them to the backend via HTTP API. This gives fine-grained control over what's collected but duplicates functionality that Wazuh or Telegraf already provide.

6. **Ollama for local AI** — AI assistant runs via Ollama (local LLM) rather than a cloud API. This keeps all data on-premises and avoids per-token costs. Default model is `gemma:2b` or `llama3.2:1b` — small models suitable for a single-server deployment.

7. **Static data files for monitoring** — DC status, NTP status, and helpdesk data are read from JSON files on disk (`/srv/jnop/data/`) rather than from a live polling system. This suggests the platform is designed to ingest data from external collectors (Telegraf, custom scripts, the Windows agent) that write JSON files, rather than polling infrastructure directly.

8. **Nginx as the sole entry point** — All traffic (frontend SPA, API, health checks) goes through nginx. The frontend container also ships its own nginx for serving the built SPA. The main nginx proxies `/api/` to the backend and serves the frontend from a shared Docker volume.

---

## Repository Structure

```
J1-NOC-Platform/
├── docker-compose.yml              # Main deployment — 10 services
├── docker-compose.override.yml     # Override: nginx ports + frontend build config
├── docker-compose.yml.bak          # Backup of previous compose config
├── .env.example                    # Template for environment variables (30 vars)
├── setup.sh                        # Simple bootstrap script (copies .env.example)
│
├── backend/                        # FastAPI backend (Python 3.12)
│   ├── app/
│   │   ├── main.py                 # App factory, router registration, v11.0.0
│   │   ├── config.py               # Pydantic Settings with DB-backed overrides
│   │   ├── database.py             # SQLAlchemy engine + session
│   │   ├── models.py               # ORM models (Role, Customer, Site, User,
│   │   │                           #   WindowsAgent, WindowsService, WindowsEvent,
│   │   │                           #   WindowsLogEntry, Tab, EncryptedSetting)
│   │   ├── schemas.py              # Pydantic schemas (Role, User, Tab, AuditLog)
│   │   ├── encryption.py           # Fernet encrypt/decrypt for settings vault
│   │   └── routers/                # API route modules
│   │       ├── auth.py             # JWT auth (bcrypt, HS256)
│   │       ├── dashboard.py        # Overview metrics from JSON data files
│   │       ├── health.py           # /healthz, /health endpoints
│   │       ├── setup.py            # First-run onboarding wizard
│   │       ├── admin.py            # CRUD for users, roles, tabs (RBAC-guarded)
│   │       ├── settings.py         # Encrypted settings CRUD
│   │       ├── wazuh.py            # Wazuh SIEM proxy + Ollama status/chat
│   │       ├── ai.py               # Ollama generate/models/chat endpoints
│   │       ├── notifications.py    # Notification router (stub)
│   │       ├── osticket.py         # osTicket helpdesk proxy
│   │       ├── static_data.py      # DC status, NTP, PBX, SSL monitoring data
│   │       ├── tools.py            # Empty router (placeholder)
│   │       └── _auth_backup.py     # Backup auth router (unused?)
│   ├── tests/
│   │   ├── test_auth.py            # Auth + health tests
│   │   └── test_dashboard.py       # Dashboard overview tests
│   ├── healthcheck.py              # Docker health check script
│   ├── requirements.txt            # 18 Python dependencies
│   ├── Dockerfile                  # python:3.12-slim
│   ├── wsgi.py                     # WSGI entry point
│   └── noc_local.db                # Local SQLite DB (dev artifact)
│
├── frontend/                       # React + Vite SPA (TypeScript)
│   ├── src/
│   │   ├── App.tsx                 # Routes: /login, /setup, /, /ldap, /snmp,
│   │   │                           #   /chrony, /tickets, /dns, /admin, /ai, /wazuh
│   │   ├── main.tsx                # Entry point
│   │   ├── pages/                  # 12 page components
│   │   ├── components/             # Layout, RequireAuth
│   │   ├── contexts/AuthContext.tsx # Auth state management
│   │   ├── services/               # API client (api.ts, adminApi.ts)
│   │   └── styles/global.css       # Global styles
│   ├── package.json                # React 18, react-router-dom, recharts, Tailwind
│   ├── vite.config.ts              # Vite config
│   ├── Dockerfile                  # Multi-stage: node:20 build → nginx:1.30.3-alpine
│   ├── nginx.conf                  # Frontend nginx config
│   └── dist/                       # Pre-built frontend (committed)
│
├── admin-service/                  # Standalone admin FastAPI service (SQLite)
│   ├── main.py                     # Admin CRUD: users, roles, tabs, notifications,
│   │                               #   integrations, onboarding, policy, tenant
│   └── README.md                   # Admin service docs
│
├── agent/
│   └── windows_agent/              # Windows monitoring agent (Python)
│       ├── main.py                 # Agent: services, events, logs, heartbeat
│       ├── config.json.example     # Agent config template
│       ├── requirements.txt        # psutil, httpx, pywin32, pyinstaller
│       ├── build.ps1               # PyInstaller build script
│       ├── install-service.ps1     # Windows service installer
│       ├── j1noc-agent.spec        # PyInstaller spec
│       └── version_info.txt        # Version metadata
│
├── database/
│   └── schema.sql                  # PostgreSQL schema (roles, customers, sites,
│                                   #   users, audit_logs) with pgcrypto
│
├── alembic/                        # Database migration framework
│   ├── env.py                      # Alembic environment config
│   └── script.py.mako              # Migration template
│   ├── alembic.ini                 # Alembic config
│
├── monitoring/
│   ├── prometheus/prometheus.yml   # Prometheus scrape config (self only)
│   ├── loki/local-config.yaml      # Loki config (filesystem storage, TSDB)
│   ├── snmp-exporter/snmp.yml      # SNMP exporter config
│   └── chrony-exporter.sh          # Chrony metrics for Prometheus textfile collector
│
├── nginx/
│   ├── nginx.conf                  # Main nginx config (worker processes, MIME, logging)
│   └── conf.d/
│       └── default.conf            # Server block: SPA + API proxy + health check
│
├── scripts/
│   ├── install.sh                  # One-command installer (Ubuntu/Debian)
│   ├── deploy.sh                   # Production deploy script (secret isolation)
│   └── sample_seed.sh              # Database seed script (tabs)
│
├── bin/
│   └── autodeploy.py               # Auto-deploy script (git push → build → deploy)
│
├── systemd/
│   └── j1-noc-platform.service     # systemd unit for Docker Compose lifecycle
│
├── docs/
│   ├── LIVE_DEPLOYMENT.md          # Production deployment guide
│   ├── PROJECT_ROADMAP.md          # 3-phase roadmap summary
│   ├── deployment-report.md        # Deployment report
│   ├── deployment-plan.md          # Deployment plan
│   ├── telegraf-windows.conf       # Telegraf config for Windows (reference)
│   └── screenshots/                # 20+ screenshots of the UI
│
├── software-development/
│   └── hermes-agent-skill-authoring/  # Hermes Agent skill (unrelated to NOC)
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # CI: Python compile + frontend build
│   │   └── codeql.yml              # CodeQL security analysis (weekly)
│   ├── dependabot.yml              # Weekly dependency updates (4 ecosystems)
│   ├── ISSUE_TEMPLATE/             # Bug report + feature request templates
│   └── PULL_REQUEST_TEMPLATE.md    # PR template
│
├── .githooks/                      # Pre-commit hooks (secret guard)
├── .gitignore
├── CHANGELOG.md                    # Minimal changelog (1 entry)
├── CODE_OF_CONDUCT.md              # Full Contributor Covenant v2.1
├── CONTRIBUTING.md                 # Minimal (1 line)
├── LICENSE                         # MIT
├── SECURITY.md                     # Template (not populated)
├── TESTING.md                      # Testing instructions
├── README.md                       # Comprehensive README
├── nginx.conf                      # Standalone nginx config (non-Docker)
└── REMOTE_VERIFY.txt               # Timestamp of last remote verification
```

---

## Notes

- **Naming discrepancy**: The README brands the project as "J1 NOC Operations Platform" with abbreviation "JNOP", while the repo is named `J1-NOC-Platform`. Docker volumes use the `jnop_` prefix. This inconsistency should be resolved to a single brand name.
- **SECURITY.md is a template**: The file contains placeholder text from GitHub's default security policy template. Version support table and vulnerability reporting instructions are not filled in.
- **CONTRIBUTING.md is minimal**: Only 1 line ("PRs are welcome. Open an issue first for major changes."). No coding standards, branch strategy, or review process documented.
- **CHANGELOG.md is minimal**: Only 1 entry dated 2026-06-13. Does not reflect the full commit history or version bumps (v11.0.0).
- **Pre-built frontend committed**: The `frontend/dist/` directory is committed to the repository, which is unusual for a project with CI that builds the frontend. This may be for quick deployment without running the build step.
- **SQLite dev artifact committed**: `backend/noc_local.db` is in the working tree — a local SQLite database that should be in `.gitignore`.
- **docker-compose.yml.bak committed**: A backup of a previous compose file is in the repo root.
- **Security audit history**: Git history shows multiple security fixes: redacted Mesh-VPN IPs and demo emails, DOM text reinterpretation fixes (CodeQL alerts #3, #4), information exposure fix (CodeQL alert #5). This indicates active security maintenance.
- **Windows Agent default NOC URL**: The agent defaults to `http://10.0.0.10` — a Mesh-VPN IP that was later redacted from the README but remains in the agent source code.
- **Hermes Agent skill in repo**: The `software-development/hermes-agent-skill-authoring/` directory contains a Hermes Agent skill definition, which is unrelated to the NOC platform's core purpose. This may have been placed here for convenience or as a development artifact.
- **No explicit backup strategy**: While Docker volumes are named and persistent, there is no documented backup/restore procedure for the PostgreSQL database or other persistent data.
- **Prometheus scrape config is minimal**: Only scrapes itself. No scrape targets for the backend, Windows agents, or other services are configured — this would need to be extended for production use.
- **Notifications router is a stub**: The `/api/notifications/send` endpoint returns `{"ok": True}` without actually sending anything. Notification integration is planned but not yet implemented.
