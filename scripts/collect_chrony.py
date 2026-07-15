#!/usr/bin/env python3
"""Collect chrony clients from the host and write to shared data directory.

This script runs on the HOST (via cron or systemd timer) because the Docker
container doesn't have ``chronyc`` installed.  It writes ntp_status.json to
the shared /srv/jnop/data volume that the backend reads.

The logic mirrors backend/app/collectors/chrony.py but is standalone so it
can run outside the container with access to chronyc and DNS.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from datetime import datetime, timezone

OUTFILE = "/srv/jnop/data/ntp_status.json"
STATUS_FILE = "/srv/jnop/data/collector_status.json"

# ── DNS reverse-lookup cache ──────────────────────────────────────────────

_dns_cache: dict[str, str] = {}


def _reverse_lookup(ip: str) -> str:
    """Reverse-DNS lookup for an IP, cached in-process."""
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


# ── Parsing ───────────────────────────────────────────────────────────────

def _parse_last_field(val: str) -> tuple[int, str]:
    """Parse the Last column from chronyc clients output.

    Returns (minutes, raw_unit) where unit is 'm' for minutes or 's' for
    seconds.  A bare number is treated as seconds.
    """
    val = val.strip()
    if val == "-" or not val:
        return (9999, "s")
    unit = "s"
    if val.endswith("m"):
        unit = "m"
        val = val[:-1]
    elif val.endswith("s"):
        unit = "s"
        val = val[:-1]
    try:
        num = int(val)
    except ValueError:
        try:
            num = int(float(val))
        except ValueError:
            return (9999, "s")
    if unit == "m":
        return (num, "m")
    return (num // 60 if num > 120 else 0, "s" if num > 60 else "s")


def _classify_status(last_min: int, last_unit: str) -> str:
    if last_unit == "m" and last_min >= 60:
        return "critical"
    if last_unit == "m" and last_min >= 30:
        return "warning"
    if last_unit == "s":
        return "ok"
    if last_min < 30:
        return "ok"
    if last_min < 60:
        return "warning"
    return "critical"


def _parse_clients_raw(raw: str) -> list[dict]:
    """Parse ``chronyc clients`` tabular output (primary — has hostnames)."""
    lines = raw.strip().split("\n")
    clients: list[dict] = []
    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        hostname = parts[0]
        if hostname in ("localhost", "127.0.0.1"):
            continue
        try:
            ntp_pkts = int(parts[1])
        except ValueError:
            ntp_pkts = 0
        try:
            drop = int(parts[2])
        except ValueError:
            drop = 0
        try:
            interval = int(parts[3]) if parts[3] != "-" else 0
        except ValueError:
            interval = 0
        last_raw = parts[5]
        last_val, last_unit = _parse_last_field(last_raw)
        status = _classify_status(last_val, last_unit)

        # Resolve bare IPs via DNS
        display_name = hostname
        ip_address = hostname
        is_ip = hostname.replace(".", "").isdigit()
        if is_ip:
            resolved = _reverse_lookup(hostname)
            if resolved != hostname:
                display_name = resolved
                ip_address = hostname
        else:
            # chronyc already resolved it; strip domain if desired
            display_name = hostname
            ip_address = hostname

        clients.append({
            "Address": ip_address,
            "Hostname": display_name,
            "Status": status,
            "NTPServer": "localhost",
            "Offset": 0.0,
            "NTPPkts": ntp_pkts,
            "Drop": drop,
            "Interval": interval,
            "Reach": 377,
            "Last": last_raw,
            "LastMin": last_val,
            "LastUnit": last_unit,
            "LastSeen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return clients


def _parse_clients_csv(raw: str) -> list[dict]:
    """Parse ``chronyc -c clients`` CSV output (fallback — IPs only)."""
    clients: list[dict] = []
    for line in raw.strip().split("\n"):
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < 6:
            continue
        ip = parts[0].strip()
        if ip in ("127.0.0.1", "localhost"):
            continue
        try:
            ntp_pkts = int(parts[1])
        except ValueError:
            ntp_pkts = 0
        try:
            drop = int(parts[2])
        except ValueError:
            drop = 0
        try:
            interval = int(parts[3]) if parts[3] != "-" else 0
        except ValueError:
            interval = 0
        try:
            reach = int(parts[4])
        except ValueError:
            reach = 0
        try:
            last_sec = int(parts[5])
        except ValueError:
            last_sec = 9999
        last_min = last_sec // 60 if last_sec < 9999 else 9999
        if last_sec >= 3600:
            status = "critical"
        elif last_sec >= 1800:
            status = "warning"
        elif last_sec > 120:
            status = "warning"
        else:
            status = "ok"
        resolved = _reverse_lookup(ip)
        display_name = resolved if resolved != ip else ip
        clients.append({
            "Address": ip,
            "Hostname": display_name,
            "Status": status,
            "NTPServer": "localhost",
            "Offset": 0.0,
            "NTPPkts": ntp_pkts,
            "Drop": drop,
            "Interval": interval,
            "Reach": reach,
            "Last": f"{last_sec}s",
            "LastMin": last_min,
            "LastUnit": "s" if last_sec < 3600 else "m",
            "LastSeen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return clients


def _record_status(name: str, ok: bool, detail: str) -> None:
    try:
        try:
            with open(STATUS_FILE) as f:
                existing = json.load(f)
        except Exception:
            existing = []
        if not isinstance(existing, list):
            existing = []
        existing = [s for s in existing if isinstance(s, dict) and s.get("name") != name]
        existing.append({
            "name": name,
            "ok": ok,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        with open(STATUS_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass


def main() -> None:
    clients: list[dict] = []

    # Primary: human-readable output (has DNS-resolved hostnames)
    try:
        result = subprocess.run(
            ["sudo", "chronyc", "clients"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            clients = _parse_clients_raw(result.stdout)
    except Exception:
        pass

    # Fallback: CSV output (IPs only)
    if not clients:
        try:
            result = subprocess.run(
                ["sudo", "chronyc", "-c", "clients"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                clients = _parse_clients_csv(result.stdout)
        except Exception:
            pass

    if clients:
        severity = {"critical": 0, "crit": 0, "warning": 1, "warn": 1, "ok": 2, "unknown": 3}
        clients.sort(key=lambda c: severity.get(c.get("Status", "ok"), 2))
        data = {"Clients": clients}
        with open(OUTFILE, "w") as f:
            json.dump(data, f, indent=2)
        _record_status("chrony", True, f"{len(clients)} clients")
        print(f"OK: wrote {len(clients)} NTP clients to {OUTFILE}")
    else:
        _record_status("chrony", False, "no client data available")
        print("ERROR: no chrony client data available", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()