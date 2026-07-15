"""Chrony NTP collector.

Queries live chrony clients via chronyc and writes operational state to
/srv/jnop/data/ntp_status.json. No secrets are handled.

The collector uses ``chronyc clients`` (human-readable) as primary source
because it includes DNS-resolved hostnames. For any IP-only entries,
a local DNS reverse lookup is performed as fallback.
"""

from __future__ import annotations

import pathlib
import socket
import subprocess
from datetime import UTC, datetime

from .base import logger, record_status, write_json

CHRONY_STATUS_FILE = "ntp_status.json"

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


# ── Parsing: human-readable ``chronyc clients`` ──────────────────────────


def _parse_last_field(val: str) -> tuple[int, str]:
    """Parse the ``Last`` column from chronyc clients output.

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
    # seconds → convert to minutes threshold
    return (num // 60 if num > 120 else 0, "s" if num > 60 else "s")


def _classify_status(last_min: int, last_unit: str) -> str:
    """Classify NTP client health based on time since last contact."""
    if last_unit == "m" and last_min >= 60:
        return "critical"
    if last_unit == "m" and last_min >= 30:
        return "warning"
    if last_unit == "s":
        return "ok"
    # For sub-minute minute values, still ok
    if last_min < 30:
        return "ok"
    if last_min < 60:
        return "warning"
    return "critical"


def _parse_clients_raw(raw: str) -> list[dict]:
    """Parse ``chronyc clients`` tabular output into structured data.

    Format::
        Hostname                      NTP   Drop Int IntL Last     Cmd   Drop Int  Last
        ===============================================================================
        hostname.k12.vi               27      0  10   -   185       0      0   -     -
        10.1.240.8                    26      0  10   -   288       0      0   -     -

    Columns (split by whitespace):
      [0] Hostname/IP   [1] NTP pkts  [2] Drop  [3] Int  [4] IntL  [5] Last  [6+] Cmd stats
    """
    lines = raw.strip().split("\n")
    clients: list[dict] = []

    for line in lines[2:]:  # Skip header + separator
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 6:
            continue

        hostname = parts[0]
        if hostname in ("localhost", "127.0.0.1"):
            continue

        # Parse NTP packet count (column 1)
        try:
            ntp_pkts = int(parts[1])
        except ValueError:
            ntp_pkts = 0

        # Parse Drop count (column 2)
        try:
            drop = int(parts[2])
        except ValueError:
            drop = 0

        # Parse poll interval (column 3)
        try:
            interval = int(parts[3]) if parts[3] != "-" else 0
        except ValueError:
            interval = 0

        # Parse Last (column 5) — seconds or minutes since last contact
        last_raw = parts[5]
        last_val, last_unit = _parse_last_field(last_raw)

        # Determine status from last contact time
        status = _classify_status(last_val, last_unit)

        # Resolve IP → hostname if needed
        # chronyc already resolves most hostnames, but bare IPs remain
        display_name = hostname
        ip_address = hostname
        if not hostname.replace(".", "").isdigit():
            # It's already a hostname — resolve to IP for the Address field
            display_name = hostname
            # Keep hostname as-is, set Address to hostname (resolved names preferred)
            ip_address = hostname
        else:
            # It's an IP — try DNS reverse lookup
            resolved = _reverse_lookup(hostname)
            if resolved != hostname:
                display_name = resolved
                ip_address = hostname

        # Calculate a human-readable "Last Seen" description
        last_desc = f"{last_val}m ago" if last_unit == "m" else f"{last_raw} ago"

        clients.append(
            {
                "Address": ip_address,
                "Hostname": display_name,
                "Status": status,
                "NTPServer": "localhost",
                "Offset": 0.0,  # Not available from 'clients' command
                "NTPPkts": ntp_pkts,
                "Drop": drop,
                "Interval": interval,
                "Reach": 377,  # Default reach (octal 377 = all 8 recent probes OK)
                "Last": last_raw,
                "LastMin": last_val,
                "LastUnit": last_unit,
                "LastSeenDesc": last_desc,
                "LastSeen": datetime.now(UTC).isoformat(timespec="seconds"),
            }
        )

    return clients


# ── Parsing: CSV ``chronyc -c clients`` ──────────────────────────────────


def _parse_clients_csv(raw: str) -> list[dict]:
    """Parse ``chronyc -c clients`` CSV output as fallback.

    CSV columns observed::
        IP, NTPPkts, Drop, Int, Reach, LastSec, DropCmd, IntCmd, ReachCmd, Timeout

    Note: CSV mode does NOT resolve hostnames and uses raw IP only.
    """
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

        # Column mapping from observed output:
        # 0=IP, 1=NTPpkts, 2=Drop, 3=Int, 4=Reach, 5=Last(sec)
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

        # Classify status
        last_min = last_sec // 60 if last_sec < 9999 else 9999
        if last_sec >= 3600:
            status = "critical"
        elif last_sec >= 1800 or last_sec > 120:
            status = "warning"
        else:
            status = "ok"

        # DNS reverse lookup for IP
        resolved = _reverse_lookup(ip)
        display_name = resolved if resolved != ip else ip

        clients.append(
            {
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
                "LastSeen": datetime.now(UTC).isoformat(timespec="seconds"),
            }
        )

    return clients


# ── Fallback: measurements log ────────────────────────────────────────────

CHRONY_LOG = pathlib.Path("/var/log/chrony/measurements.log")


def _read_from_log() -> list[dict]:
    """Read client data from chrony measurements log as last-resort fallback."""
    clients: list[dict] = []
    try:
        if not CHRONY_LOG.exists():
            return []
        content = CHRONY_LOG.read_text().split("\n")[-200:]
        seen: set[str] = set()
        for line in content:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                ip = parts[1]
                if ip in seen or ip in ("localhost", "127.0.0.1"):
                    continue
                seen.add(ip)
                try:
                    offset = float(parts[2])
                    status = (
                        "ok"
                        if abs(offset) < 100
                        else "warning"
                        if abs(offset) < 500
                        else "critical"
                    )
                except ValueError:
                    offset = 0.0
                    status = "ok"

                resolved = _reverse_lookup(ip)
                display_name = resolved if resolved != ip else ip

                clients.append(
                    {
                        "Address": ip,
                        "Hostname": display_name,
                        "Status": status,
                        "NTPServer": "localhost",
                        "Offset": round(offset, 2),
                        "NTPPkts": 0,
                        "Drop": 0,
                        "Interval": 0,
                        "Reach": 377,
                        "Last": "unknown",
                        "LastMin": 9999,
                        "LastUnit": "m",
                        "LastSeen": datetime.now(UTC).isoformat(timespec="seconds"),
                    }
                )
    except Exception:
        pass
    return clients


# ── Main collector ─────────────────────────────────────────────────────────


def collect() -> None:
    """Collect live chrony client status and write to ntp_status.json.

    When running inside the Docker container (no chronyc available), this
    is a no-op — the host-side systemd timer (jnop-chrony-collector.timer)
    writes ntp_status.json every 60s via scripts/collect_chrony.py.
    """
    import shutil

    # Skip entirely if chronyc is not available (e.g. inside container)
    if not shutil.which("chronyc"):
        logger.debug(
            "chronyc not found — skipping in-container collection (host timer writes data)"
        )
        record_status("chrony", True, "host-side collection")
        return

    clients: list[dict] = []

    # Primary: human-readable output (has DNS-resolved hostnames)
    try:
        result = subprocess.run(
            ["sudo", "chronyc", "clients"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            clients = _parse_clients_raw(result.stdout)
    except Exception:
        pass

    # Fallback: CSV output (IPs only, but has per-packet metrics)
    if not clients:
        try:
            result = subprocess.run(
                ["sudo", "chronyc", "-c", "clients"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                clients = _parse_clients_csv(result.stdout)
        except Exception:
            pass

    # Last resort: log parsing
    if not clients:
        clients = _read_from_log()

    if clients:
        # Sort: critical first, then warning, then ok
        severity = {"critical": 0, "crit": 0, "warning": 1, "warn": 1, "ok": 2, "unknown": 3}
        clients.sort(key=lambda c: severity.get(c.get("Status", "ok"), 2))

        data = {"Clients": clients}
        write_json(CHRONY_STATUS_FILE, data)
        record_status("chrony", True, f"{len(clients)} clients")
    else:
        record_status("chrony", False, "no client data available")
