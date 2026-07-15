"""LDAP directory collector.

Binds to LDAP_URL with LDAP_BIND_DN / LDAP_BIND_PASSWORD from the vault and
reports directory health (reachable, server info). Writes operational state
(no bind DN or password) to /srv/jnop/data/directory_status.json.
ldap3 is optional; if absent the collector records a status and returns.
"""

from __future__ import annotations

from .base import get_cred, logger, mask, record_status, write_json


def collect() -> None:
    url = get_cred("LDAP_URL")
    bind_dn = get_cred("LDAP_BIND_DN")
    password = get_cred("LDAP_BIND_PASSWORD")
    domain = get_cred("LDAP_DOMAIN", "")
    if not url:
        record_status("ldap", False, "no LDAP_URL configured")
        return
    logger.info("LDAP collect: url=%s bind_dn=%s", url, mask(bind_dn))
    try:
        from ldap3 import ALL, Connection, Server
    except Exception:
        record_status("ldap", False, "ldap3 not installed")
        return
    try:
        server = Server(url, get_info=ALL)
        with Connection(
            server,
            user=bind_dn or "",
            password=password or "",
            auto_bind=True,
            raise_exceptions=True,
        ) as conn:
            info = getattr(server, "info", None)
            vendor = (getattr(info, "vendor_name", "") or "") if info else ""
            write_json(
                "directory_status.json",
                {
                    "url": url,
                    "domain": domain,
                    "reachable": True,
                    "vendor": str(vendor)[:80],
                    "bound": bool(conn.bound),
                    "collected_at": __import__("datetime")
                    .datetime.now(__import__("datetime").timezone.utc)
                    .isoformat(),
                },
            )
            record_status("ldap", True, f"bound to {url}")
    except Exception as e:
        logger.exception("LDAP collect failed for %s", url)
        record_status("ldap", False, f"bind error: {type(e).__name__}")
