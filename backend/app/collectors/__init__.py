"""Collector registry and runner.

Importing this package must never fail, even if optional deps (pysnmp, ldap3)
are missing — each collector guards its own imports. ``run_all`` is safe to call
from a background loop; it never raises.
"""
from __future__ import annotations

import logging

from . import snmp, ldap, wazuh, osticket

logger = logging.getLogger("jnop.collectors")

_REGISTRY = (snmp, ldap, wazuh, osticket)


def run_all() -> dict:
    """Run every collector once and return a status map. Never raises."""
    out: dict = {}
    for mod in _REGISTRY:
        name = mod.__name__.split(".")[-1]
        try:
            mod.collect()
            out[name] = "ran"
        except Exception as e:  # backstop; collectors self-handle
            logger.exception("collector %s crashed", name)
            out[name] = f"error: {type(e).__name__}"
    return out
