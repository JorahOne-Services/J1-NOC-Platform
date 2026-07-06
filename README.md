<!-- j1-brand:v2 -->
<div align="center">

# J1-NOC-Platform

An enterprise-grade NOC dashboard with real-time infrastructure monitoring, SIEM integration, AI-powered diagnostics, and operational automation — all behind `docker compose up`.

[![GitHub](https://img.shields.io/badge/github-OneByJorah%2FJ1--NOC--Platform-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah/J1-NOC-Platform)
[![License](https://img.shields.io/badge/license-MIT-FFB300?style=for-the-badge&labelColor=0d0d0c)](LICENSE)
[![Language](https://img.shields.io/badge/HTML-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![Built by](https://img.shields.io/badge/built%20by-JorahOne%20LLC-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah)

</div>

---

## Why This Exists

Enterprise NOC tools are expensive, complex, and locked into vendor ecosystems. J1-NOC-Platform is a self-hosted alternative that monitors DNS, NTP, Domain Controllers, and OS image deployment — with Wazuh SIEM integration for security event correlation, an Ollama-powered AI assistant for diagnostics, and RBAC for multi-tenant access.

## Key Features

| Feature | Why It Matters |
|---|---|
| Real-time infrastructure monitoring | DNS, NTP, DC replication, PBX — all on one screen |
| Wazuh SIEM integration | Security event correlation alongside operational data |
| Ollama AI assistant | Ask natural-language questions about your infrastructure |
| RBAC with encrypted vault | Role-based access with secrets stored securely |
| React + Vite frontend | Modern, fast UI with real-time updates |
| One-command setup | `sudo ./setup.sh` for Ubuntu/Debian, or `docker compose up -d` |

## Quick Start

```bash
git clone https://github.com/OneByJorah/J1-NOC-Platform.git
cd J1-NOC-Platform

# Automated setup (Ubuntu/Debian)
sudo ./setup.sh

# Manual Docker
docker compose up -d
```

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend    │◀───▶│  Backend      │────▶│  PostgreSQL   │
│  React/Vite  │     │  FastAPI      │     │               │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │  Wazuh   │  │  Ollama  │  │  Admin   │
       │  SIEM     │  │  AI Diag │  │  (RBAC)  │
       └──────────┘  └──────────┘  └──────────┘
```

## Documentation

| Doc | Description |
|---|---|
| [Setup Guide](docs/setup.md) | Installation and configuration |
| [Monitoring Modules](docs/monitoring.md) | Configuring DNS, NTP, DC, and PBX monitors |
| [SIEM Integration](docs/siem.md) | Connecting Wazuh for security event correlation |

---

## License

MIT © JorahOne, LLC — see [LICENSE](LICENSE)

<sub>Part of the JorahOne infrastructure ecosystem.</sub>
