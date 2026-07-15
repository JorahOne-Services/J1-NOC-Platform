# J1-NOC-Platform — Windows Deployment Guide

Run the full J1 NOC Platform stack on Windows using Docker Desktop.
All services (backend, frontend, admin, postgres, redis, grafana, prometheus, loki, crowdsec, snmp-exporter) run in containers — no WSL or Linux VM needed beyond Docker Desktop itself.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| **OS** | Windows 10 64-bit (Build 19041+) | Windows 11 |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 20 GB free | 40 GB free |
| **Docker Desktop** | v4.25+ | Latest |
| **Git** | v2.40+ | Latest |

---

## 1. Install Docker Desktop

1. Download from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Run the installer — enable **WSL 2 backend** when prompted
3. After install, open Docker Desktop → **Settings → Resources**:
   - CPUs: 4+ (8 ideal)
   - Memory: 6 GB+ (12 GB ideal)
   - Disk: 30 GB+
4. Restart Docker Desktop

Verify in **PowerShell**:
```powershell
docker --version
docker compose version
```

---

## 2. Clone the Repository

```powershell
cd C:\
git clone https://github.com/OneByJorah/NexusCore.git J1-NOC-Platform
cd J1-NOC-Platform
```

> **Note:** Replace the URL above with your actual repo if different.

---

## 3. Configure Secrets

Create the environment file **`.env`** in the project root. Copy from the template:

```powershell
copy .env.example .env
```

Then edit `.env` with your real credentials. On Windows, use any editor:

```powershell
notepad .env
```

**Critical values to change:**

| Variable | Set To |
|---|---|
| `SECRET_KEY` | A long random string (32+ chars) |
| `POSTGRES_PASSWORD` | Strong password for PostgreSQL |
| `REDIS_PASSWORD` | Strong password for Redis |
| `GRAFANA_ADMIN_PASSWORD` | Strong password for Grafana |
| `DATABASE_URL` | `postgresql+psycopg2://jnop:<POSTGRES_PASSWORD>@postgres:5432/jnop` |
| `REDIS_URL` | `redis://:<REDIS_PASSWORD>@redis:6379/0` |

Optional integrations (leave empty/defaults if not using):
- `LDAP_*` — Active Directory / LDAP credentials
- `WAZUH_*` — Wazuh SIEM API credentials
- `OSTICKET_*` — osTicket helpdesk API key
- `MITEL_SNMP_*` — Mitel PBX SNMP settings

> **⚠️ Never commit `.env` to git.** The `.gitignore` already excludes it, and the pre-push hook will block it.

---

## 4. Windows Compatibility — docker-compose.win.yml

Docker Compose on Windows has a few differences from Linux. A **`docker-compose.win.yml`** override file handles these automatically. It's included in the repo — no manual steps needed.

Key differences it handles:
- **No `host.docker.internal` override** — Docker Desktop for Windows provides this automatically
- **CrowdSec volume mounts** — Windows doesn't have `/var/log/auth.log` or `/var/log/syslog`, so these are replaced with Docker logging
- **Volume paths** — Windows uses named volumes instead of host bind mounts for data persistence

---

## 5. Launch the Stack

```powershell
# Build and start all services
docker compose -f docker-compose.yml -f docker-compose.win.yml up -d --build
```

First build takes 5–10 minutes (downloads base images, installs Python/Node deps).

Watch the logs:
```powershell
docker compose logs -f backend
```

---

## 6. Verify Everything is Running

```powershell
# Check all containers
docker compose ps

# Quick health checks
curl http://localhost/healthz          # Backend health
curl http://localhost:3000/api/health  # Grafana
curl http://localhost:8081/api/health   # Admin service
```

Expected `docker compose ps` output (all healthy):
```
NAME                STATUS                  PORTS
jnop-backend        Up (healthy)            8000/tcp
jnop-frontend       Up (healthy)            80/tcp
jnop-nginx          Up (healthy)            0.0.0.0:80->80/tcp
jnop-postgres       Up (healthy)            5432/tcp
jnop-redis          Up (healthy)            6379/tcp
jnop-grafana        Up (healthy)            0.0.0.0:3000->3000/tcp
jnop-prometheus     Up (healthy)            0.0.0.0:9090->9090/tcp
jnop-loki           Up (healthy)            0.0.0.0:3100->3100/tcp
jnop-admin          Up (healthy)            8081/tcp
jnop-crowdsec       Up                      -
jnop-snmp-exporter  Up                      9116/tcp
```

---

## 7. Access the Dashboard

| Service | URL |
|---|---|
| **J1 NOC Dashboard** | [http://localhost](http://localhost) |
| **Admin Panel** | [http://localhost/admin/](http://localhost/admin/) |
| **Grafana** | [http://localhost:3000](http://localhost:3000) |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) |
| **Loki** | [http://localhost:3100](http://localhost:3100) |

---

## 8. Create Admin User (First Run Only)

```powershell
# Create the initial admin user
docker compose exec backend python -c "from app.database import engine; from app.auth import create_user; create_user('admin', 'YourStrongPassword!', 'admin')"
```

Or use the onboarding page at [http://localhost](http://localhost) if it's the first launch.

---

## 9. Run Database Migrations

```powershell
docker compose exec backend alembic upgrade head
```

---

## 10. Development Workflow

### Frontend Development (Hot Reload)

For frontend development with live reload on Windows:

```powershell
cd frontend
npm install
npm run dev
```

This starts the Vite dev server on `http://localhost:5173` with hot module replacement.
The backend API is still served by Docker at `http://localhost/api/`.

### Backend Development

Backend changes require a rebuild:
```powershell
docker compose up -d --build backend
```

### Running Tests

```powershell
# Install test dependencies on host (one-time)
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pytest pytest-cov pytest-asyncio
pytest tests/ -v -o addopts=""
```

Or inside the container:
```powershell
docker compose exec backend pip install pytest pytest-cov pytest-asyncio
docker compose exec backend pytest tests/ -v -o addopts=""
```

---

## 11. Stopping & Cleaning

```powershell
# Stop all services
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

---

## 12. Updating

```powershell
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.win.yml up -d --build
```

---

## Troubleshooting

### Port Conflicts
If port 80 is in use (IIS, Skype, etc.):
```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Option A: Stop the conflicting service
# Option B: Change the port in docker-compose.win.yml
```

To use port 8080 instead of 80, edit `docker-compose.win.yml` and change:
```yaml
ports:
  - "8080:80"    # instead of "80:80"
```

### Docker Desktop WSL Issues
```powershell
# Reset Docker Desktop (last resort)
wsl --shutdown
# Restart Docker Desktop from Start Menu
```

### Container Won't Start
```powershell
# Check logs for a specific service
docker compose logs backend
docker compose logs postgres

# Rebuild from scratch
docker compose build --no-cache backend
docker compose up -d backend
```

### PostgreSQL Connection Refused
If `postgres` isn't ready when `backend` starts:
```powershell
docker compose restart backend
```

The `depends_on: condition: service_healthy` should handle this, but manual restart works too.

### CrowdSec on Windows
CrowdSec lacks Linux log files on Windows. It still runs for metrics collection but security event detection is limited. To disable it:
```powershell
docker compose -f docker-compose.yml -f docker-compose.win.yml up -d --build --scale crowdsec=0
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Windows Host (Docker Desktop)                │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │  nginx   │──▶│ frontend │   │ backend  │──▶│ postgres │   │
│  │  :80     │   │  (SPA)   │   │  :8000   │   │  :5432   │   │
│  └──────────┘   └──────────┘   └────┬─────┘   └──────────┘   │
│       │                              │                          │
│       │         ┌──────────┐   ┌────┴─────┐                  │
│       │         │  redis   │◀──│  admin   │                  │
│       │         │  :6379   │   │  :8081   │                  │
│       │         └──────────┘   └──────────┘                  │
│       │                                                       │
│       ├──▶ Grafana (:3000)   Prometheus (:9090)               │
│       ├──▶ Loki (:3100)      SNMP Exporter (:9116)            │
│       └──▶ CrowdSec (metrics only on Windows)                │
│                                                                 │
│  Browser ──▶ http://localhost ──▶ J1 NOC Dashboard           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Notes

- **`.env` is gitignored** — secrets never enter the repo
- **Pre-push hook** (`.githooks/pre-push`) blocks accidental secret commits
- **gitleaks** CI scans every push for leaked credentials
- **Production secret injection** — in production, secrets come from `/etc/j1-noc-platform/.env.live`; on Windows, they stay in your local `.env`
- **No real customer data** — use example.com/10.0.x.x/192.0.2.x for test fixtures only