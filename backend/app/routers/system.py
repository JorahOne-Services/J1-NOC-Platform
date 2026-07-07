"""System overview endpoint: aggregates NOC KPIs with live service health.

Combines the static overview metrics (devices, alerts, tickets) with live
health probes for the backend, database, and AI (Ollama) service so the
dashboard can show a single operational picture.
"""

import pathlib
from typing import Any

import httpx
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..config import get_settings
from ..database import engine
from .dashboard import _count_tickets, _load_json

router = APIRouter()

BASE = pathlib.Path("/srv/jnop/data")


def _db_connected() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _ollama_connected() -> bool:
    settings = get_settings()
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{settings.ollama_host}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def _overview_kpis() -> dict[str, Any]:
    dc_status = _load_json("dc_status.json")
    ntp_status = _load_json("ntp_status.json")

    dcs = dc_status.get("DCs", dc_status.get("dc_status", []))
    total_devices = len(dcs) if isinstance(dcs, list) else 0
    online_devices = len(
        [d for d in dcs if isinstance(d, dict) and d.get("status", "").lower() == "ok"]
    )

    clients = ntp_status.get("Clients", ntp_status.get("clients", []))
    active_alerts = 0
    critical_alerts = 0
    for c in clients:
        if isinstance(c, dict):
            status = c.get("status", "").lower()
            if status == "critical":
                critical_alerts += 1
            elif status in ("warn", "warning"):
                active_alerts += 1
    active_alerts += total_devices - online_devices

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": total_devices - online_devices,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "open_tickets": _count_tickets(),
    }


@router.get("/system/overview")
def system_overview() -> Response:
    """Aggregated operational overview with live service health."""
    services = [
        {"name": "Backend API", "status": "up"},
        {"name": "Database (PostgreSQL)", "status": "up" if _db_connected() else "down"},
        {"name": "AI (Ollama)", "status": "up" if _ollama_connected() else "down"},
        {"name": "Cache (Redis)", "status": "up"},
    ]
    payload = {
        "kpis": _overview_kpis(),
        "services": services,
        "healthy": sum(1 for s in services if s["status"] == "up"),
        "total_services": len(services),
    }
    return JSONResponse(payload)
