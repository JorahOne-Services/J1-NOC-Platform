"""SNMP collector for Mitel PBX / network devices.

When running inside the Docker container (no snmpget/snmpwalk), this is a
no-op — the host-side systemd timer runs scripts/collect_snmp.py which
writes pbx_status.json to the shared /srv/jnop/data volume.
"""

from __future__ import annotations

import shutil

from .base import record_status


def collect() -> None:
    """Container-side no-op. SNMP collection runs on the host via systemd."""
    if shutil.which("snmpget") is None:
        record_status("snmp", True, "host-side collector (no snmpget in container)")
        return
    # If snmpget IS available (host-side), this would be the place to call
    # the collection logic, but scripts/collect_snmp.py handles that.
    record_status("snmp", True, "deferred to host-side collector")
