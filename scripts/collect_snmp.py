#!/usr/bin/env python3
"""SNMP collector for Mitel PBX / network devices (10.11.224.10-15).

Runs on the HOST via systemd timer. Collects:
  - System: sysDescr, sysUpTime, sysName, sysContact, sysLocation, sysOID
  - Host Resources: CPU load, memory, disk usage, process count
  - Network: interfaces, IP addresses, TCP/UDP stats
  - Mitel Enterprise: alarms, slot status (OID 1.3.6.1.4.1.1027)
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
from datetime import datetime, timezone

OUTFILE = "/srv/jnop/data/pbx_status.json"
STATUS_FILE = "/srv/jnop/data/collector_status.json"

# ── Device targets ────────────────────────────────────────────────────────

DEVICES = [
    {"host": "10.11.224.10", "role": "gateway"},
    {"host": "10.11.224.11", "role": "controller"},
    {"host": "10.11.224.12", "role": "gateway"},
    {"host": "10.11.224.13", "role": "controller"},
    {"host": "10.11.224.14", "role": "gateway"},
    {"host": "10.11.224.15", "role": "controller"},
]

COMMUNITY = "public"
SNMP_TIMEOUT = 2
SNMP_RETRIES = 0

# ── OIDs ──────────────────────────────────────────────────────────────────

SYSTEM_OIDS = {
    "sysDescr":    "1.3.6.1.2.1.1.1.0",
    "sysUpTime":   "1.3.6.1.2.1.1.3.0",
    "sysName":     "1.3.6.1.2.1.1.5.0",
    "sysContact":  "1.3.6.1.2.1.1.4.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
    "sysServices": "1.3.6.1.2.1.1.7.0",
}

# Host Resources MIB (HR-MIB)
HR_OIDS = {
    "hrSystemUptime":    "1.3.6.1.2.1.25.1.1.0",
    "hrSystemProcesses": "1.3.6.1.2.1.25.1.6.0",
    "hrMemorySize":      "1.3.6.1.2.1.25.2.3.1.5.1",   # Physical memory total (in units)
    "hrMemoryUsed":      "1.3.6.1.2.1.25.2.3.1.6.1",   # Physical memory used
    "hrMemoryUnits":     "1.3.6.1.2.1.25.2.3.1.4.1",   # Memory allocation units (bytes)
}

WALK_OIDS = {
    # Interfaces
    "ifDescr":       "1.3.6.1.2.1.2.2.1.2",
    "ifType":        "1.3.6.1.2.1.2.2.1.3",
    "ifSpeed":       "1.3.6.1.2.1.2.2.1.5",
    "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus":  "1.3.6.1.2.1.2.2.1.8",
    "ifInOctets":    "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets":   "1.3.6.1.2.1.2.2.1.16",
    # IP addresses
    "ipAdEntAddr":    "1.3.6.1.2.1.4.20.1.1",
    "ipAdEntNetMask":  "1.3.6.1.2.1.4.20.1.3",
    # Host Resources: Storage (disks)
    "hrStorageDescr": "1.3.6.1.2.1.25.2.3.1.3",
    "hrStorageUnits":  "1.3.6.1.2.1.25.2.3.1.4",
    "hrStorageSize":   "1.3.6.1.2.1.25.2.3.1.5",
    "hrStorageUsed":   "1.3.6.1.2.1.25.2.3.1.6",
    # Host Resources: CPU
    "hrCpuLoad": "1.3.6.1.2.1.25.3.3.1.2",
    # Host Resources: Process names
    "hrSWRunName": "1.3.6.1.2.1.25.4.2.1.2",
    # TCP listeners
    "tcpConnLocalPort": "1.3.6.1.2.1.6.13.1.1",
    # UDP listeners
    "udpLocalPort": "1.3.6.1.2.1.7.5.1.1",
}

# TCP/UDP scalar stats
TCP_UDP_OIDS = {
    "tcpCurrEstab": "1.3.6.1.2.1.6.9.0",
    "tcpActiveOpens": "1.3.6.1.2.1.6.5.0",
    "tcpInSegs": "1.3.6.1.2.1.6.10.0",
    "tcpOutSegs": "1.3.6.1.2.1.6.11.0",
    "tcpRetransSegs": "1.3.6.1.2.1.6.12.0",
}

# Mitel Enterprise OIDs (1.3.6.1.4.1.1027)
MITEL_OIDS = {
    "mitelAlarmsActive": "1.3.6.1.4.1.1027.4.1.1.2.1.2.1.0",
    "mitelAlarmsMajor":  "1.3.6.1.4.1.1027.4.1.1.2.1.2.2.0",
    "mitelAlarmsMinor":  "1.3.6.1.4.1.1027.4.1.1.2.1.2.3.0",
    "mitelAlarmsInfo":   "1.3.6.1.4.1.1027.4.1.1.2.1.2.4.0",
    "mitelSlotsTotal":   "1.3.6.1.4.1.1027.4.1.1.2.1.3.0",
    "mitelSlotsAvail":   "1.3.6.1.4.1.1027.4.1.1.2.1.4.0",
    "mitelVersion":      "1.3.6.1.4.1.1027.4.1.1.2.1.5.0",
}

IFSTATUS_MAP = {1: "up", 2: "down", 3: "testing", 4: "unknown", 5: "dormant", 6: "notPresent", 7: "lowerLayerDown"}
ADMINSTATUS_MAP = {1: "up", 2: "down", 3: "testing"}

# ── DNS cache ──────────────────────────────────────────────────────────────

_dns_cache: dict[str, str] = {}


def _reverse_lookup(ip: str) -> str:
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


# ── SNMP helpers ───────────────────────────────────────────────────────────

def _snmp_get(host: str, oid: str) -> str | None:
    try:
        r = subprocess.run(
            ["snmpget", "-v2c", "-c", COMMUNITY, "-t", str(SNMP_TIMEOUT),
             "-r", str(SNMP_RETRIES), host, oid],
            capture_output=True, text=True, timeout=SNMP_TIMEOUT + 3,
        )
        line = r.stdout.strip()
        if "No Such" in line or "Error" in line or not line:
            return None
        if "=" in line:
            val_part = line.split("=", 1)[1].strip()
            if val_part.startswith('"') or "STRING:" in val_part:
                val = val_part.split(":", 1)[1].strip().strip('"') if ":" in val_part else val_part.strip('"')
                return val
            if ":" in val_part:
                val = val_part.split(":", 1)[1].strip()
                return val
            return val_part
        return None
    except Exception:
        return None


def _snmp_walk(host: str, oid: str) -> dict[str, str]:
    results: dict[str, str] = {}
    try:
        r = subprocess.run(
            ["snmpwalk", "-v2c", "-c", COMMUNITY, "-t", str(SNMP_TIMEOUT),
             "-r", str(SNMP_RETRIES), host, oid],
            capture_output=True, text=True, timeout=SNMP_TIMEOUT * 2 + 5,
        )
        base_iso = "iso." + oid.lstrip(".").lstrip("1.").lstrip(".")
        prefixes = [oid + ".", oid.lstrip(".") + ".", base_iso + "."]
        for line in r.stdout.strip().splitlines():
            if "No Such" in line or "Error" in line or "Timeout" in line:
                continue
            if "=" not in line:
                continue
            oid_part, val_part = line.split("=", 1)
            oid_part = oid_part.strip()
            val_part = val_part.strip()
            suffix = None
            for prefix in prefixes:
                if oid_part.startswith(prefix):
                    suffix = oid_part[len(prefix):]
                    break
            if suffix is None:
                continue
            if ":" in val_part:
                val = val_part.split(":", 1)[1].strip().strip('"')
            else:
                val = val_part.strip('"')
            results[suffix] = val
    except Exception:
        pass
    return results


def _is_reachable(host: str, timeout: float = 1.5) -> bool:
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", str(int(timeout)), host],
            capture_output=True, timeout=timeout + 1,
        )
        return r.returncode == 0
    except Exception:
        return False


def _parse_uptime_ticks(ticks_str: str | None) -> dict:
    if not ticks_str:
        return {"raw": None, "days": 0, "hours": 0, "minutes": 0, "seconds": 0, "human": "unknown"}
    m = re.search(r"\((\d+)\)\s*(\d+):(\d+):(\d+):(\d+)", ticks_str)
    if m:
        ticks = int(m.group(1))
        return {"raw": ticks, "days": int(m.group(2)), "hours": int(m.group(3)),
                "minutes": int(m.group(4)), "seconds": int(m.group(5)),
                "human": f"{int(m.group(2))}d {int(m.group(3))}h {int(m.group(4))}m"}
    m2 = re.search(r"\((\d+)\)\s*(\d+):(\d+):(\d+)", ticks_str)
    if m2:
        ticks = int(m2.group(1))
        d, rem = divmod(ticks // 100, 86400)
        h, rem2 = divmod(rem, 3600)
        m, s = divmod(rem2, 60)
        return {"raw": ticks, "days": d, "hours": h, "minutes": m, "seconds": s, "human": f"{d}d {h}h {m}m"}
    try:
        ticks = int(float(ticks_str))
        secs = ticks // 100
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        return {"raw": ticks, "days": d, "hours": h, "minutes": m, "seconds": s, "human": f"{d}d {h}h {m}m"}
    except (ValueError, TypeError):
        return {"raw": ticks_str, "days": 0, "hours": 0, "minutes": 0, "seconds": 0, "human": ticks_str}


def _parse_mitel_descr(descr: str | None) -> dict:
    if not descr:
        return {}
    info: dict[str, str] = {}
    for part in descr.split(";"):
        part = part.strip()
        if ":" in part:
            key, val = part.split(":", 1)
            key = key.strip(); val = val.strip()
            if key == "VerAg": info["agent_version"] = val
            elif key == "VerHw": info["hardware"] = val
            elif key == "VerSw": info["software_version"] = val
            elif key == "VerPl": info["platform"] = val; info["model"] = val
            elif key == "VerMCD": info["mcd_version"] = val
    if not info:
        info["raw_descr"] = descr[:120]
    return info


def _parse_storage(storages: dict) -> list[dict]:
    """Parse HR-MIB storage entries into a list of disk/memory info."""
    result = []
    for idx, descr in storages.get("hrStorageDescr", {}).items():
        if descr in ("Physical memory", "Virtual memory", "Memory buffers",
                     "Cached memory", "Shared memory", "Swap space"):
            # Memory entries
            units = int(storages.get("hrStorageUnits", {}).get(idx, "1024"))
            size = int(storages.get("hrStorageSize", {}).get(idx, "0"))
            used = int(storages.get("hrStorageUsed", {}).get(idx, "0"))
            total_mb = round(size * units / 1048576, 1)
            used_mb = round(used * units / 1048576, 1)
            pct = round(used / size * 100, 1) if size > 0 else 0
            result.append({
                "type": "memory", "name": descr, "index": idx,
                "size_mb": total_mb, "used_mb": used_mb, "used_pct": pct,
                "units": units, "size_blocks": size, "used_blocks": used,
            })
        elif descr.startswith("/"):
            # Disk entries
            units = int(storages.get("hrStorageUnits", {}).get(idx, "4096"))
            size = int(storages.get("hrStorageSize", {}).get(idx, "0"))
            used = int(storages.get("hrStorageUsed", {}).get(idx, "0"))
            total_gb = round(size * units / 1073741824, 2)
            used_gb = round(used * units / 1073741824, 2)
            pct = round(used / size * 100, 1) if size > 0 else 0
            result.append({
                "type": "disk", "name": descr, "index": idx,
                "size_gb": total_gb, "used_gb": used_gb, "used_pct": pct,
                "units": units, "size_blocks": size, "used_blocks": used,
            })
    return result


# ── Main collector ──────────────────────────────────────────────────────────

def collect() -> None:
    entries: list[dict] = []
    up_count = 0
    down_count = 0

    for device in DEVICES:
        host = device["host"]
        role = device.get("role", "unknown")
        hostname = _reverse_lookup(host)

        # Quick reachability check
        if not _is_reachable(host):
            entries.append({
                "host": host, "hostname": hostname, "name": hostname,
                "role": role, "status": "down", "sysDescr": None,
                "sysUpTime": {"raw": None, "days": 0, "hours": 0, "minutes": 0, "seconds": 0, "human": "unreachable"},
                "interfaceCount": 0, "ipAddresses": [], "interfaces": [],
                "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            down_count += 1
            continue

        # SNMP liveness check
        sys_name_test = _snmp_get(host, SYSTEM_OIDS["sysName"])
        if sys_name_test is None:
            entries.append({
                "host": host, "hostname": hostname, "name": hostname,
                "role": role, "status": "snmp_timeout", "sysDescr": None,
                "sysUpTime": {"raw": None, "days": 0, "hours": 0, "minutes": 0, "seconds": 0, "human": "SNMP timeout"},
                "interfaceCount": 0, "ipAddresses": [], "interfaces": [],
                "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            down_count += 1
            continue

        # ── System ────────────────────────────────────────────────────────
        system: dict[str, str | None] = {}
        for name, oid in SYSTEM_OIDS.items():
            system[name] = _snmp_get(host, oid)

        sys_name = system.get("sysName") or hostname
        descr = system.get("sysDescr", "")
        uptime_info = _parse_uptime_ticks(system.get("sysUpTime"))
        mitel_info = _parse_mitel_descr(descr)

        # ── Host Resources ────────────────────────────────────────────────
        hr: dict[str, str | None] = {}
        for name, oid in HR_OIDS.items():
            hr[name] = _snmp_get(host, oid)

        processes = int(hr.get("hrSystemProcesses") or "0")
        mem_units = int(hr.get("hrMemoryUnits") or "1024")
        mem_total = int(hr.get("hrMemorySize") or "0")
        mem_used = int(hr.get("hrMemoryUsed") or "0")
        mem_total_mb = round(mem_total * mem_units / 1048576, 1)
        mem_used_mb = round(mem_used * mem_units / 1048576, 1)
        mem_pct = round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0

        # CPU load per core
        cpu_loads = _snmp_walk(host, WALK_OIDS["hrCpuLoad"])
        cpu_cores = []
        for core_id, load in cpu_loads.items():
            cpu_cores.append({"core": core_id, "load_pct": int(load) if load.isdigit() else load})
        cpu_avg = round(sum(int(c["load_pct"]) for c in cpu_cores if str(c["load_pct"]).isdigit()) / max(len(cpu_cores), 1), 1) if cpu_cores else 0

        # ── Storage (disks/memory) ────────────────────────────────────────
        storage_walks = {}
        for key in ("hrStorageDescr", "hrStorageUnits", "hrStorageSize", "hrStorageUsed"):
            storage_walks[key] = _snmp_walk(host, WALK_OIDS[key])
        storage_list = _parse_storage(storage_walks)

        # ── Interfaces ────────────────────────────────────────────────────
        if_descr = _snmp_walk(host, WALK_OIDS["ifDescr"])
        if_speed = _snmp_walk(host, WALK_OIDS["ifSpeed"])
        if_oper = _snmp_walk(host, WALK_OIDS["ifOperStatus"])
        if_admin = _snmp_walk(host, WALK_OIDS["ifAdminStatus"])
        if_in = _snmp_walk(host, WALK_OIDS["ifInOctets"])
        if_out = _snmp_walk(host, WALK_OIDS["ifOutOctets"])

        interfaces = []
        for idx, name_val in if_descr.items():
            if name_val == "lo":
                continue
            oper_raw = if_oper.get(idx, "?")
            admin_raw = if_admin.get(idx, "?")
            oper_status = IFSTATUS_MAP.get(int(oper_raw), oper_raw) if oper_raw.isdigit() else str(oper_raw)
            admin_status = ADMINSTATUS_MAP.get(int(admin_raw), admin_raw) if admin_raw.isdigit() else str(admin_raw)
            try:
                speed = int(if_speed.get(idx, "0"))
                speed_human = f"{speed // 1_000_000_000} Gbps" if speed >= 1_000_000_000 else f"{speed // 1_000_000} Mbps" if speed >= 1_000_000 else f"{speed // 1000} Kbps"
            except (ValueError, TypeError):
                speed_human = if_speed.get(idx, "?")
            interfaces.append({
                "index": idx, "name": name_val,
                "operStatus": oper_status, "adminStatus": admin_status,
                "speed": if_speed.get(idx, "0"), "speed_human": speed_human,
                "inOctets": if_in.get(idx, "0"), "outOctets": if_out.get(idx, "0"),
            })

        # ── IP Addresses ──────────────────────────────────────────────────
        ip_addrs = _snmp_walk(host, WALK_OIDS["ipAdEntAddr"])
        ip_masks = _snmp_walk(host, WALK_OIDS["ipAdEntNetMask"])
        ip_list = []
        for idx, addr in ip_addrs.items():
            if addr == "127.0.0.1" or addr.startswith("0."):
                continue
            ip_list.append({"address": addr, "mask": ip_masks.get(idx, "?")})

        # ── TCP/UDP ────────────────────────────────────────────────────────
        tcp_udp: dict[str, str | None] = {}
        for name, oid in TCP_UDP_OIDS.items():
            tcp_udp[name] = _snmp_get(host, oid)

        tcp_listeners_raw = _snmp_walk(host, WALK_OIDS["tcpConnLocalPort"])
        # Extract just the port numbers from TCP listener OIDs
        tcp_ports = set()
        for oid_suffix in tcp_listeners_raw:
            # oid_suffix like "0.0.0.0.80.0.0.0.0.0" — last number is the port
            parts = oid_suffix.split(".")
            if len(parts) >= 2:
                try:
                    tcp_ports.add(int(parts[-1]))
                except ValueError:
                    pass
        udp_ports_raw = _snmp_walk(host, WALK_OIDS["udpLocalPort"])
        udp_ports = set()
        for oid_suffix in udp_ports_raw:
            parts = oid_suffix.split(".")
            if parts:
                try:
                    udp_ports.add(int(parts[-1]))
                except ValueError:
                    pass

        # ── Mitel Enterprise ───────────────────────────────────────────────
        mitel: dict[str, str | None] = {}
        for name, oid in MITEL_OIDS.items():
            mitel[name] = _snmp_get(host, oid)

        # ── Process names (top Mitel-related) ─────────────────────────────
        proc_names_raw = _snmp_walk(host, WALK_OIDS["hrSWRunName"])
        processes_list = []
        for pid, name in proc_names_raw.items():
            if any(kw in name.lower() for kw in ("mitel", "mcd", "3300", "eod", "smdr", "vm", "sip", "phone", "call")):
                processes_list.append({"pid": pid, "name": name})

        status = "healthy"
        up_count += 1

        entry = {
            "host": host, "hostname": hostname, "name": sys_name, "role": role,
            "status": status,
            "sysDescr": descr,
            **mitel_info,
            "sysUpTime": uptime_info,
            "sysContact": system.get("sysContact"),
            "sysLocation": system.get("sysLocation"),
            "sysServices": system.get("sysServices"),
            # Host Resources
            "processes": processes,
            "cpu_cores": cpu_cores,
            "cpu_avg": cpu_avg,
            "memory": {
                "total_mb": mem_total_mb, "used_mb": mem_used_mb,
                "used_pct": mem_pct, "units": mem_units,
            },
            "storage": storage_list,
            # Network
            "interfaceCount": len(interfaces),
            "ipAddresses": ip_list,
            "interfaces": interfaces,
            "tcp_connections": int(tcp_udp.get("tcpCurrEstab") or "0"),
            "tcp_active_opens": int(tcp_udp.get("tcpActiveOpens") or "0"),
            "tcp_in_segs": int(tcp_udp.get("tcpInSegs") or "0"),
            "tcp_out_segs": int(tcp_udp.get("tcpOutSegs") or "0"),
            "tcp_retrans_segs": int(tcp_udp.get("tcpRetransSegs") or "0"),
            "tcp_ports": sorted(tcp_ports),
            "udp_ports": sorted(udp_ports),
            # Mitel Enterprise
            "mitel_alarms": {
                "active": int(mitel.get("mitelAlarmsActive") or "0"),
                "major": int(mitel.get("mitelAlarmsMajor") or "0"),
                "minor": int(mitel.get("mitelAlarmsMinor") or "0"),
                "info": int(mitel.get("mitelAlarmsInfo") or "0"),
            },
            "mitel_slots_total": mitel.get("mitelSlotsTotal"),
            "mitel_slots_available": mitel.get("mitelSlotsAvail"),
            "mitel_version": mitel.get("mitelVersion"),
            # Mitel-related processes
            "mitel_processes": processes_list,
            "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        entries.append(entry)

    data = {"devices": entries, "total": len(entries), "up": up_count, "down": down_count}
    with open(OUTFILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Record status
    try:
        try:
            existing = json.loads(open(STATUS_FILE).read())
        except Exception:
            existing = []
        if not isinstance(existing, list):
            existing = []
        existing = [s for s in existing if isinstance(s, dict) and s.get("name") != "snmp"]
        existing.append({
            "name": "snmp", "ok": True,
            "detail": f"{up_count} up, {down_count} down of {len(entries)} devices",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        with open(STATUS_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass

    print(f"OK: wrote {len(entries)} devices ({up_count} up, {down_count} down) to {OUTFILE}")


if __name__ == "__main__":
    collect()