from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json
import pathlib

router = APIRouter()
BASE = pathlib.Path('/srv/jnop/data')
LOG_DIR = pathlib.Path('/srv/jnop/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)


@router.get('/dc_status')
def dc_status():
    p = BASE / 'dc_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        data = payload.get('DCs') or payload.get('dc_status') or []
    elif isinstance(payload, list):
        data = payload
    else:
        data = []
    return JSONResponse(data)


@router.get('/ntp_status')
def ntp_status():
    p = BASE / 'ntp_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    return JSONResponse(payload or {})


@router.get('/ntp_clients')
def ntp_clients():
    p = BASE / 'ntp_status.json'
    data = {}
    try:
        data = json.loads(p.read_text()) or {}
    except Exception:
        data = {}
    clients = data.get('Clients') or data.get('clients') or data.get('ntp_clients') or []
    return JSONResponse(clients)


@router.post('/dc/forcerepl')
async def force_repl(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})


@router.get('/tags')
def tags():
    return JSONResponse([])


@router.post('/generate')
async def generate(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})


@router.get('/gcds-sample.log', include_in_schema=False)
@router.get('/dc_replication_monitor.txt', include_in_schema=False)
def serve_logs():
    return PlainTextResponse('log placeholder')


# ── PBX / Mitel SNMP endpoints ──────────────────────────────────────────────

@router.get('/pbx/status')
def pbx_status():
    return JSONResponse([
        {
            "host": "10.0.1.12", "name": "Mitel-MX-2500-A", "model": "MX 2500",
            "status": "healthy", "uptime_pct": 99.2, "uptime_since": "2026-06-01T00:00:00Z",
            "cpu": 35, "cpu_cores": 4, "cpu_mhz": 2400,
            "memory": 33, "ram_used": 2.9, "ram_total": 8.0,
            "disk": 20, "disk_used": 160.5, "disk_total": 500.0,
            "active_calls": 201, "registrations": 115,
            "trunks_active": 11, "trunks_total": 11,
        },
        {
            "host": "10.0.2.45", "name": "Mitel-MX-2500-B", "model": "MX 2500",
            "status": "degraded", "uptime_pct": 87.5, "uptime_since": "2026-06-01T00:00:00Z",
            "cpu": 66, "cpu_cores": 4, "cpu_mhz": 2400,
            "memory": 83, "ram_used": 2.1, "ram_total": 8.0,
            "disk": 78, "disk_used": 82.8, "disk_total": 500.0,
            "active_calls": 151, "registrations": 91,
            "trunks_active": 13, "trunks_total": 14,
        },
        {
            "host": "10.0.3.12", "name": "Mitel-3300-C", "model": "3300",
            "status": "degraded", "uptime_pct": 87.5, "uptime_since": "2026-06-01T00:00:00Z",
            "cpu": 61, "cpu_cores": 4, "cpu_mhz": 2400,
            "memory": 79, "ram_used": 2.9, "ram_total": 8.0,
            "disk": 50, "disk_used": 138.4, "disk_total": 500.0,
            "active_calls": 155, "registrations": 105,
            "trunks_active": 14, "trunks_total": 16,
        },
    ])


@router.get('/pbx/snmp/walk')
def pbx_snmp_walk():
    return JSONResponse({"entries": [
        {"host": "10.0.1.12", "oid": "1.3.6.1.2.1.1.3.0", "description": "sysUpTime",
         "value": "1234567", "unit": "centiseconds", "timestamp": "2026-06-14 12:40:00", "status": "ok"},
        {"host": "10.0.1.12", "oid": "1.3.6.1.4.1.1066.1.1.1", "description": "mitelCallActive",
         "value": "201", "unit": "calls", "timestamp": "2026-06-14 12:40:00", "status": "ok"},
        {"host": "10.0.2.45", "oid": "1.3.6.1.4.1.1066.1.1.2", "description": "mitelTrunkStatus",
         "value": "1 of 2 trunks down", "unit": "", "timestamp": "2026-06-14 12:39:55", "status": "warn"},
        {"host": "10.0.3.12", "oid": "1.3.6.1.4.1.1066.1.1.3", "description": "mitelRegFailures",
         "value": "3", "unit": "events", "timestamp": "2026-06-14 12:39:50", "status": "warn"},
    ]})


# ── SSL / Certificate Monitoring ─────────────────────────────────────────────

SSL_DOMAINS = [
    {"domain": "noc-server.k12.vi", "issuer": "Let's Encrypt", "expires": "2026-09-15T00:00:00Z",
     "days_left": 92, "status": "ok", "san": ["noc-server.k12.vi", "noc-server"]},
    {"domain": "vide-k12.vi", "issuer": "Let's Encrypt", "expires": "2026-08-20T00:00:00Z",
     "days_left": 66, "status": "ok", "san": ["vide.k12.vi", "www.vide.k12.vi"]},
    {"domain": "dck12vi.vide.k12.vi", "issuer": "Let's Encrypt", "expires": "2026-07-01T00:00:00Z",
     "days_left": 16, "status": "warn", "san": ["dck12vi.vide.k12.vi"]},
    {"domain": "mail.vide.k12.vi", "issuer": "Let's Encrypt", "expires": "2026-12-10T00:00:00Z",
     "days_left": 178, "status": "ok", "san": ["mail.vide.k12.vi"]},
    {"domain": "vpn.vide.k12.vi", "issuer": "Self-Signed", "expires": "2025-12-01T00:00:00Z",
     "days_left": -195, "status": "critical", "san": ["vpn.vide.k12.vi"]},
]

SSL_RESPONSE_TIMES = [
    {"domain": "noc-server.k12.vi", "ms": 42, "status": "ok"},
    {"domain": "vide.k12.vi", "ms": 88, "status": "ok"},
    {"domain": "dck12vi.vide.k12.vi", "ms": 31, "status": "ok"},
    {"domain": "mail.vide.k12.vi", "ms": 156, "status": "ok"},
    {"domain": "vpn.vide.k12.vi", "ms": 0, "status": "down"},
]


@router.get('/ssl/certs')
def ssl_certs():
    return JSONResponse(SSL_DOMAINS)


@router.get('/ssl/response')
def ssl_response():
    return JSONResponse(SSL_RESPONSE_TIMES)
