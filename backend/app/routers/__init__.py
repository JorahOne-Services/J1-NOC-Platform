from __future__ import annotations

from importlib import import_module

ROUTER_MODULES: dict[str, str] = {
    "health": "health",
    "auth": "auth",
    "dashboard": "dashboard",
    "notifications": "notifications",
    "tools": "tools",
    "ai": "ai",
    "admin": "admin",
    "static_data": "static_data",
    "agent": "agent",
    "helpdesk": "osticket",
    "system": "system",
}


def load_routers():
    loaded = {}
    for name, module in ROUTER_MODULES.items():
        mod = import_module(f".{module}", __name__)
        loaded[name] = mod
    return loaded


__all__ = list(ROUTER_MODULES.keys())
