from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json
import pathlib

router = APIRouter()
BASE = pathlib.Path('/srv/jnop/data')
LOG_DIR = pathlib.Path('/srv/jnop/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)


@router.get('/dc_status')
def dc_status():
    p = BASE / 'dc_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        data = payload.get('DCs') or payload.get('dc_status') or []
    elif isinstance(payload, list):
        data = payload
    else:
        data = []
    return JSONResponse(data)


@router.get('/ntp_status')
def ntp_status():
    p = BASE / 'ntp_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    return JSONResponse(payload or {})


@router.get('/ntp_clients')
def ntp_clients():
    p = BASE / 'ntp_status.json'
    data = {}
    try:
        data = json.loads(p.read_text()) or {}
    except Exception:
        data = {}
    clients = data.get('Clients') or data.get('clients') or data.get('ntp_clients') or []
    return JSONResponse(clients)


@router.post('/dc/forcerepl')
async def force_repl(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})


@router.get('/tags')
def tags():
    return JSONResponse([])


@router.post('/generate')
async def generate(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})


@router.get('/gcds-sample.log', include_in_schema=False)
@router.get('/dc_replication_monitor.txt', include_in_schema=False)
def serve_logs():
    # Tiny text/plain response so the frontend doesn't fail fetch() casing
    return PlainTextResponse('log placeholder')


# Simulated PBX / Mitel SNMP endpoints for dashboard demo
PBX_HOSTS = [
    {"host": "10.0.1.12", "name": "Mitel-MX-2500-A", "model": "MX 2500"},
    {"host": "10.0.2.45", "name": "Mitel-MX-2500-B", "model": "MX 2500"},
    {"host": "10.0.3.12", "name": "Mitel-3300-C", "model": "3300"},
]

PBX_STATUSES = ["healthy", "healthy", "healthy", "degraded", "critical"]


def _pick_status(seed: str):
    idx = sum(ord(c) for c in seed) % len(PBX_STATUSES)
    return PBX_STATUSES[idx]


@router.get('/pbx/status')
def pbx_status():
    import random
    random.seed(42)
    data = []
    for host in PBX_HOSTS:
        status = _pick_status(host["host"])
        is_healthy = status == "healthy"
        is_degraded = status == "degraded"
        uptime = 99.2 if is_healthy else (87.5 if is_degraded else 62.1)
        cpu = random.randint(15, 45) if is_healthy else random.randint(45, 75)
        memory = random.randint(30, 60) if is_healthy else random.randint(60, 85)
        disk = random.randint(20, 50) if is_healthy else random.randint(50, 80)
        active_calls = random.randint(12, 220)
        registrations = random.randint(80, 150)
        trunks_total = random.randint(8, 16)
        trunks_active = trunks_total - (0 if is_healthy else random.randint(1, 3))
        data.append({
            "host": host["host"],
            "name": host["name"],
            "model": host["model"],
            "status": status,
            "uptime_pct": uptime,
            "uptime_since": "2026-06-01T00:00:00Z",
            "cpu": cpu,
            "cpu_cores": 4,
            "cpu_mhz": 2400,
            "memory": memory,
            "ram_used": round(random.uniform(2.0, 6.0), 1),
            "ram_total": 8.0,
            "disk": disk,
            "disk_used": round(random.uniform(50.0, 200.0), 1),
            "disk_total": 500.0,
            "active_calls": active_calls,
            "registrations": registrations,
            "trunks_active": trunks_active,
            "trunks_total": trunks_total,
        })
    return JSONResponse(data)


@router.get('/pbx/snmp/walk')
def pbx_snmp_walk():
    host = "10.0.1.12"
    return JSONResponse({
  host: {
   "sysDescr": "Mitel MX 2500",
   "sysUpTime": 1234567,
   "ifNumber": 6,
   "ifDescr": ["eth0", "eth1", "ppp0", "vlan10", "vlan20", "vlan99"],
   "ifOperStatus": [1, 1, 2, 1, 1, 2],
   "ifInOctets": [123456789, 987654321, 0, 456789123, 321654987, 0],
   "ifOutOctets": [987654321, 123456789, 0, 321654987, 456789123, 0],
   "ssosID": ["101", "102", "103", "104", "105", "106"],
   "ssosTrying": [0, 0, 1, 0, 0, 1],
   "ssosActive": [45, 120, 0, 80, 210, 0],
   "snmpEnableAuthenTraps": 1,
   "snmpInPkts": 54321,
   "snmpOutPkts": 54319,
   "snmpInBadVersions": 0,
   "snmpInBadCommunityNames": 0,
   "snmpInBadUses": 0,
   "snmpInASNParseErrs": 0,
   "snmpSilentDrops": 0,
   "snmpProxyDrops": 0,
   "snmpTrapOID": ["1.3.6.1.6.3.1.1.4.1.0", "1.3.6.1.6.3.1.1.4.1.0"],
   "snmpTrapEnterprises": [".1.3.6.1.4.1.1066", ".1.3.6.1.4.1.1066"],
   "snmpTrapGeneric": ["coldStart", "authenticationFailure"],
   "snmpTrapSpecific": [0, 0],
   "snmpTrapTimeStamp": [0, 0],
   "snmpTrapVarBinds": [
    ["1.3.6.1.2.1.1.3.0", "0:0:00:05.00"],
    ["1.3.6.1.2.1.1.3.0", "0:0:00:12.00"]
   ],
   "snmpTrapCommunity": ["public", "public"],
   "snmpTrapSource": ["10.0.1.12", "10.0.1.12"],
   "snmpTrapDest": ["10.0.1.100", "10.0.1.100"],
   "snmpTrapEngineId": ["80:00:77:06:01:02:03:04:05", "80:00:77:06:01:02:03:04:05"],
   "snmpTrapUserName": ["", ""],
   "snmpTrapContextName": ["", ""],
   "snmpTrapContextEngineId": ["", ""],
   "snmpTrapAuthentication": [0, 0],
   "snmpTrapPrivacy": [0, 0],
   "snmpTrapAuthSalt": ["", ""],
   "snmpTrapPrivSalt": ["", ""],
   "snmpTrapReport": ["", ""]
  }
 })
