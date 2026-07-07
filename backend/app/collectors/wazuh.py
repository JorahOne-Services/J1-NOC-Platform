"""Wazuh SIEM collector.

Queries WAZUH_API_URL with WAZUH_USERNAME / WAZUH_PASSWORD from the vault and
reports active alert counts. Writes /srv/jnop/data/siem_status.json (no
credentials). Uses httpx (already a backend dependency).
"""
from __future__ import annotations

import json

from .base import get_cred, mask, write_json, record_status, logger


def collect() -> None:
    base = get_cred("WAZUH_API_URL")
    user = get_cred("WAZUH_USERNAME", "wazuh")
    password = get_cred("WAZUH_PASSWORD", "wazuh")
    verify_ssl = str(get_cred("WAZUH_VERIFY_SSL", "false")).lower() in ("1", "true", "yes")
    if not base:
        record_status("wazuh", False, "no WAZUH_API_URL configured")
        return
    logger.info("Wazuh collect: url=%s user=%s", base, mask(user))
    try:
        import httpx

        with httpx.Client(timeout=10, verify=verify_ssl) as c:
            auth = (user, password)
            alerts = c.get(f"{base.rstrip('/')}/security/alerts", auth=auth)
            agents = c.get(f"{base.rstrip('/')}/agents", auth=auth)
            alert_count = 0
            if alerts.status_code == 200:
                try:
                    alert_count = len(alerts.json().get("data", {}).get("affected_items", []))
                except Exception:
                    alert_count = 0
            agent_total = 0
            if agents.status_code == 200:
                try:
                    agent_total = len(agents.json().get("data", {}).get("affected_items", []))
                except Exception:
                    agent_total = 0
        write_json(
            "siem_status.json",
            {
                "url": base,
                "active_alerts": alert_count,
                "agents": agent_total,
                "collected_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
            },
        )
        record_status("wazuh", True, f"{alert_count} alerts, {agent_total} agents")
    except Exception as e:
        logger.exception("Wazuh collect failed for %s", base)
        record_status("wazuh", False, f"api error: {type(e).__name__}")
