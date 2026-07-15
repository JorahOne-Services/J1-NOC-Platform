"""osTicket helpdesk collector.

Queries OSTICKET_BASE_URL with OSTICKET_API_KEY from the vault and writes the
ticket list to /srv/jnop/data/helpdesk_tickets.json. That file is what the
dashboard overview reads for its open_tickets KPI, so this collector makes the
ticket count live. Credentials are passed only as the X-API-Key header and are
never written to disk or logs.
"""

from __future__ import annotations

from .base import get_cred, logger, mask, record_status, write_json


def collect() -> None:
    base = get_cred("OSTICKET_BASE_URL")
    key = get_cred("OSTICKET_API_KEY")
    if not base or not key:
        record_status("osticket", False, "osTicket not configured")
        return
    logger.info("osTicket collect: base=%s key=%s", base, mask(key))
    try:
        import httpx

        with httpx.Client(timeout=10, headers={"X-API-Key": key}) as c:
            r = c.get(f"{base.rstrip('/')}/api/tickets.json")
            r.raise_for_status()
            payload = r.json()
        tickets = payload.get("tickets", []) if isinstance(payload, dict) else payload
        if not isinstance(tickets, list):
            tickets = []
        write_json("helpdesk_tickets.json", tickets)
        open_count = len(
            [
                t
                for t in tickets
                if str(t.get("status", "")).lower() in ("open", "new", "in progress")
            ]
        )
        record_status("osticket", True, f"{len(tickets)} tickets, {open_count} open")
    except Exception as e:
        logger.exception("osTicket collect failed for %s", base)
        record_status("osticket", False, f"api error: {type(e).__name__}")
