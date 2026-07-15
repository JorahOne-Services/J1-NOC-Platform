import contextlib
import json
import pathlib
import socket
from functools import lru_cache

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter()
BASE = pathlib.Path("/srv/jnop/data")
LOG_DIR = pathlib.Path("/srv/jnop/logs")

# ── DNS reverse-lookup cache ────────────────────────────────────────────────

_dns_cache: dict[str, str] = {}


@lru_cache(maxsize=512)
def _reverse_lookup(ip: str) -> str:
    """Resolve an IP to a hostname via DNS; cached in-process."""
    if ip in _dns_cache:
        return _dns_cache[ip]
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        fqdn = name.rstrip(".")
        _dns_cache[ip] = fqdn
        return fqdn
    except (socket.herror, socket.gaierror, OSError):
        _dns_cache[ip] = ip
        return ip


def _enrich_hostname(entry: dict) -> dict:
    """Add Hostname to a client/DC dict via DNS if missing."""
    if "Hostname" not in entry or not entry["Hostname"]:
        ip = entry.get("Address") or entry.get("IPAddress", "")
        if ip:
            entry = {**entry, "Hostname": _reverse_lookup(ip)}
    return entry


# Defensive: only create if writable (non-root user may not own the parent)
with contextlib.suppress(OSError):
    LOG_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/dc_status")
def dc_status():
    p = BASE / "dc_status.json"
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        data = payload.get("DCs") or payload.get("dc_status") or []
    elif isinstance(payload, list):
        data = payload
    else:
        data = []
    # Enrich with DNS hostnames
    data = [_enrich_hostname(d) for d in data]
    return JSONResponse(data)


@router.get("/ntp_status")
def ntp_status():
    p = BASE / "ntp_status.json"
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    # Enrich clients with DNS hostnames
    if isinstance(payload, dict):
        clients = (
            payload.get("Clients") or payload.get("clients") or payload.get("ntp_clients") or []
        )
        payload["Clients"] = [_enrich_hostname(c) for c in clients if isinstance(c, dict)]
    return JSONResponse(payload or {})


@router.get("/ntp_clients")
def ntp_clients():
    p = BASE / "ntp_status.json"
    data = {}
    try:
        data = json.loads(p.read_text()) or {}
    except Exception:
        data = {}
    clients = data.get("Clients") or data.get("clients") or data.get("ntp_clients") or []
    return JSONResponse([_enrich_hostname(c) for c in clients if isinstance(c, dict)])


@router.post("/dc/forcerepl")
async def force_repl(request: Request):
    body = await request.json()
    return JSONResponse({"Success": True, "Request": body})


@router.get("/tags")
def tags():
    return JSONResponse([])


@router.post("/generate")
async def generate(request: Request):
    body = await request.json()
    return JSONResponse({"Success": True, "Request": body})


@router.get("/gcds-sample.log", include_in_schema=False)
@router.get("/dc_replication_monitor.txt", include_in_schema=False)
def serve_logs():
    return PlainTextResponse("log placeholder")


# ── PBX / Mitel SNMP endpoints ──────────────────────────────────────────────


def _load_pbx() -> list[dict]:
    """Load live PBX data from the SNMP collector output."""
    p = BASE / "pbx_status.json"
    try:
        payload = json.loads(p.read_text())
    except Exception:
        return []
    if isinstance(payload, dict):
        return payload.get("devices", [])
    if isinstance(payload, list):
        return payload
    return []


@router.get("/pbx/status")
def pbx_status():
    devices = _load_pbx()
    if not devices:
        return JSONResponse([])
    # Enrich with DNS hostnames where missing
    for d in devices:
        if not d.get("hostname") or d["hostname"] == d.get("host"):
            d["hostname"] = _reverse_lookup(d.get("host", ""))
    return JSONResponse(devices)


@router.get("/pbx/snmp/walk")
def pbx_snmp_walk():
    devices = _load_pbx()
    if not devices:
        return JSONResponse({"devices": [], "entries": []})
    # Build a flat walk-like structure from the live data
    entries = []
    for d in devices:
        host = d.get("host", "")
        # System OIDs
        for key in ("sysName", "sysDescr", "sysUpTime", "sysContact", "sysLocation"):
            val = d.get(key)
            if val:
                if isinstance(val, dict):
                    val = val.get("human", str(val))
                entries.append(
                    {
                        "host": host,
                        "hostname": d.get("hostname", host),
                        "oid": f"sys.{key}",
                        "description": key,
                        "value": str(val),
                        "status": d.get("status", "unknown"),
                        "collected_at": d.get("collected_at", ""),
                    }
                )
        # Interface entries
        for iface in d.get("interfaces", []):
            entries.append(
                {
                    "host": host,
                    "hostname": d.get("hostname", host),
                    "oid": f"ifDescr.{iface.get('index', '?')}",
                    "description": f"Interface {iface.get('name', '?')}",
                    "value": f"{iface.get('operStatus', '?')} / {iface.get('speed_human', '?')}",
                    "status": "ok" if iface.get("operStatus") == "up" else "warn",
                    "collected_at": d.get("collected_at", ""),
                }
            )
    return JSONResponse({"devices": devices, "entries": entries})


# ── SSL / Certificate Monitoring ─────────────────────────────────────────────

SSL_DOMAINS = [
    {
        "domain": "www.example.com",
        "issuer": "Let's Encrypt",
        "expires": "2026-09-15T00:00:00Z",
        "days_left": 92,
        "status": "ok",
        "san": ["www.example.com", "example.com"],
    },
    {
        "domain": "api.example.com",
        "issuer": "Let's Encrypt",
        "expires": "2026-08-20T00:00:00Z",
        "days_left": 66,
        "status": "ok",
        "san": ["api.example.com"],
    },
    {
        "domain": "mail.example.com",
        "issuer": "Let's Encrypt",
        "expires": "2026-07-01T00:00:00Z",
        "days_left": 16,
        "status": "warn",
        "san": ["mail.example.com"],
    },
    {
        "domain": "cdn.example.com",
        "issuer": "Let's Encrypt",
        "expires": "2026-12-10T00:00:00Z",
        "days_left": 178,
        "status": "ok",
        "san": ["cdn.example.com", "static.example.com"],
    },
    {
        "domain": "vpn.example.com",
        "issuer": "Self-Signed",
        "expires": "2025-12-01T00:00:00Z",
        "days_left": -195,
        "status": "critical",
        "san": ["vpn.example.com"],
    },
    {
        "domain": "dev.example.com",
        "issuer": "Let's Encrypt",
        "expires": "2026-10-05T00:00:00Z",
        "days_left": 112,
        "status": "ok",
        "san": ["dev.example.com", "staging.example.com"],
    },
]

SSL_RESPONSE_TIMES = [
    {"domain": "www.example.com", "ms": 42, "status": "ok"},
    {"domain": "api.example.com", "ms": 88, "status": "ok"},
    {"domain": "mail.example.com", "ms": 31, "status": "ok"},
    {"domain": "cdn.example.com", "ms": 156, "status": "ok"},
    {"domain": "vpn.example.com", "ms": 0, "status": "down"},
    {"domain": "dev.example.com", "ms": 67, "status": "ok"},
]


# ── 90-day uptime heatmap (Tianji-inspired) ──────────────────────────────────
# Generates deterministic but realistic-looking uptime data
def _gen_uptime(days=90):
    import hashlib

    data = []
    for i in range(days):
        d = (24 * 60 * 60 * 1000) * (days - 1 - i)
        ts = 1718409600000 - d  # anchored to ~Jun 2024
        seed = hashlib.md5(str(ts).encode()).hexdigest()
        r = int(seed[:2], 16) / 255.0
        if r > 0.97:
            status = "down"
        elif r > 0.9:
            status = "degraded"
        else:
            status = "ok"
        data.append({"ts": ts, "status": status})
    return data


SSL_UPTIME = {
    "www.example.com": _gen_uptime(),
    "api.example.com": _gen_uptime(),
    "mail.example.com": _gen_uptime(),
    "cdn.example.com": _gen_uptime(),
    "vpn.example.com": _gen_uptime(),
    "dev.example.com": _gen_uptime(),
}


@router.get("/ssl/certs")
def ssl_certs():
    return JSONResponse(SSL_DOMAINS)


@router.get("/ssl/response")
def ssl_response():
    return JSONResponse(SSL_RESPONSE_TIMES)


@router.get("/ssl/uptime")
def ssl_uptime():
    return JSONResponse(SSL_UPTIME)
