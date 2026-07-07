"""SNMP collector for Mitel PBX / network devices.

Reads MITEL_SNMP_HOST and MITEL_SNMP_COMMUNITY from the vault, polls a handful
of standard OIDs, and writes operational state (never the community string) to
/srv/jnop/data/pbx_status.json. pysnmp is optional; if absent the collector
records a status and returns without error.
"""
from __future__ import annotations

from .base import get_cred, mask, write_json, record_status, logger

MITEL_OIDS = {
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysDescr": "1.3.6.1.2.1.1.1.0",
}


def _snmp_get(host: str, community: str, oid: str, timeout: float = 4.0):
    from pysnmp.hlapi import (
        CommunityData,
        ContextData,
        ObjectType,
        ObjectIdentity,
        UdpTransportTarget,
        getCmd,
    )

    iterator = getCmd(
        CommunityData(community, mpModel=1),
        UdpTransportTarget((host, 161), timeout=timeout, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    error_indication, _error_status, _error_index, var_binds = next(iterator)
    if error_indication:
        raise RuntimeError(str(error_indication))
    for var_bind in var_binds:
        return var_bind[1].prettyPrint()
    return None


def collect() -> None:
    host = get_cred("MITEL_SNMP_HOST")
    community = get_cred("MITEL_SNMP_COMMUNITY", "public")
    if not host or host in ("localhost", "127.0.0.1", ""):
        record_status("snmp", False, "no SNMP host configured")
        return
    logger.info("SNMP collect: host=%s community=%s", host, mask(community))
    try:
        _ = __import__("pysnmp")
    except Exception:
        record_status("snmp", False, "pysnmp not installed")
        return
    try:
        result = {}
        for name, oid in MITEL_OIDS.items():
            try:
                result[name] = _snmp_get(host, community, oid)
            except Exception as e:  # one OID failing shouldn't abort the rest
                logger.warning("SNMP %s failed: %s", name, e)
        uptime = result.get("sysUpTime")
        entries = [
            {
                "host": host,
                "name": result.get("sysName") or host,
                "model": (result.get("sysDescr") or "")[:80],
                "status": "ok",
                "sys_uptime": uptime,
                "collected_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
            }
        ]
        write_json("pbx_status.json", entries)
        record_status("snmp", True, f"polled {host}")
    except Exception as e:
        logger.exception("SNMP poll failed for %s", host)
        record_status("snmp", False, f"poll error: {type(e).__name__}")
