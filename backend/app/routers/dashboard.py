import json
import pathlib
import socket
from functools import lru_cache

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
BASE = pathlib.Path("/srv/jnop/data")

# ── DNS reverse-lookup cache (process-lifetime) ─────────────────────────

_dns_cache: dict[str, str] = {}


@lru_cache(maxsize=512)
def _reverse_lookup(ip: str) -> str:
    """Resolve an IP to a hostname via DNS; cache in-process."""
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


def _load_json(filename: str) -> dict:
    """Load JSON data from data directory, return empty dict on failure."""
    p = BASE / filename
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _count_tickets() -> int:
    """Return open ticket count from helpdesk data."""
    try:
        tickets = _load_json("helpdesk_tickets.json")
        if isinstance(tickets, list):
            return len(
                [
                    t
                    for t in tickets
                    if t.get("status", "").lower() in ("open", "in progress", "new")
                ]
            )
    except Exception:
        pass
    return 0


@router.get("/dashboard/overview")
def dashboard_overview():
    """Return platform overview metrics for the dashboard home page."""
    dc_status = _load_json("dc_status.json")
    ntp_status = _load_json("ntp_status.json")

    # Count devices from DC status — resolve IPs to hostnames
    dcs = dc_status.get("DCs", dc_status.get("dc_status", []))
    total_devices = len(dcs) if isinstance(dcs, list) else 0
    online_devices = 0
    resolved_dcs = []
    for d in dcs:
        if not isinstance(d, dict):
            continue
        if d.get("Status", "").lower() == "ok":
            online_devices += 1
        # Add DNS hostname for each DC
        ip = d.get("IPAddress", "")
        hostname = d.get("Hostname") or d.get("DCName", "")
        if ip and not hostname:
            hostname = _reverse_lookup(ip)
        entry = {**d, "Hostname": hostname}
        resolved_dcs.append(entry)

    # Count NTP clients and derive alerts
    clients_raw = ntp_status.get("Clients", ntp_status.get("clients", []))
    clients = []
    active_alerts = 0
    critical_alerts = 0
    for c in clients_raw:
        if not isinstance(c, dict):
            continue
        status = c.get("Status", "").lower()
        if status in ("critical", "crit"):
            critical_alerts += 1
        elif status in ("warn", "warning"):
            active_alerts += 1

        # Add DNS hostname if not already present
        ip = c.get("Address", "")
        hostname = c.get("Hostname", "")
        if ip and not hostname:
            hostname = _reverse_lookup(ip)
        clients.append({**c, "Hostname": hostname})

    active_alerts += total_devices - online_devices  # offline DCs

    open_tickets = _count_tickets()

    return JSONResponse(
        {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "open_tickets": open_tickets,
            "dcs": resolved_dcs,
            "ntp_clients": clients,
        }
    )
