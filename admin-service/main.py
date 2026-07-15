import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Any
from cryptography.fernet import Fernet

import uvicorn
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = "/srv/jnop/admin-service/admin.sqlite"
# Encryption key derived from SECRET_KEY env var
_ENCRYPTION_KEY = None

def _get_cipher():
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is None:
        raw = os.environ.get("SECRET_KEY", "change-me-in-production")
        # Pad or truncate to 32 bytes for Fernet
        raw = raw.ljust(32, 'Z')[:32]
        import base64
        _ENCRYPTION_KEY = Fernet(base64.urlsafe_b64encode(raw.encode()))
    return _ENCRYPTION_KEY

def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _get_cipher().encrypt(plaintext.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _get_cipher().decrypt(ciphertext.encode()).decode()
    except Exception:
        return "[encrypted]"

app = FastAPI(title="J1 NOC Admin Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            full_name TEXT,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_active INTEGER NOT NULL DEFAULT 1,
            is_locked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            label TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_visible INTEGER NOT NULL DEFAULT 1,
            icon TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            target TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            config_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            config_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """,
    )
    con.commit()
    # seed default admin if empty
    cur.execute("SELECT count(*) FROM users")
    if cur.fetchone()[0] == 0:
        hashed = hashlib.sha256("admin".encode()).hexdigest()
        cur.execute(
            "INSERT INTO users(username,email,full_name,hashed_password,role) VALUES(?,?,?,?,?)",
            ("admin", None, "Administrator", hashed, "admin"),
        )
        con.commit()
    con.close()

init_db()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, username, hashed_password, role, is_locked FROM users WHERE username=?", (req.username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return {"ok": False, "error": "invalid"}
    uid, uname, hashed, role, locked = row
    if locked:
        return {"ok": False, "error": "locked"}
    if hashlib.sha256(req.password.encode()).hexdigest() != hashed:
        return {"ok": False, "error": "invalid"}
    sid = secrets.token_hex(16)
    exp = (datetime.utcnow() + timedelta(hours=8)).isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO sessions(id, username, expires_at) VALUES(?,?,?)", (sid, uname, exp))
    con.commit()
    con.close()
    return {
        "ok": True,
        "token": sid,
        "user": {"id": uid, "username": uname, "role": role},
    }


@app.post("/api/auth/logout")
def logout():
    return Response({"ok":True})


@app.get("/api/admin/tabs")
def get_tabs():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,path,label,sort_order,is_visible,icon FROM tabs ORDER BY sort_order")
    rows = cur.fetchall()
    con.close()
    return {
        "tabs": [
            {
                "id": r[0],
                "path": r[1],
                "label": r[2],
                "sort_order": r[3],
                "is_visible": bool(r[4]),
                "icon": r[5],
            }
            for r in rows
        ],
    }


@app.post("/api/admin/tabs")
def create_tab(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO tabs(path,label,sort_order,is_visible,icon) VALUES(?,?,?,?,?)",
        (
            payload.get("path", "/tab"),
            payload.get("label", "Tab"),
            payload.get("sort_order", 0),
            1 if payload.get("is_visible", True) else 0,
            payload.get("icon"),
        ),
    )
    con.commit()
    tid = cur.lastrowid
    con.close()
    return {"id": tid}


@app.put("/api/admin/tabs/{tab_id}")
def update_tab(tab_id: int, payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sets = []
    args = []
    for field in ["path", "label", "sort_order", "icon"]:
        if field in payload:
            sets.append(f"{field}=?")
            args.append(payload[field])
    if "is_visible" in payload:
        sets.append("is_visible=?")
        args.append(1 if payload["is_visible"] else 0)
    if sets:
        args.append(tab_id)
        cur.execute(f"UPDATE tabs SET {', '.join(sets)} WHERE id=?", args)
        con.commit()
    con.close()
    return {"updated": tab_id}


@app.delete("/api/admin/tabs/{tab_id}")
def delete_tab(tab_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM tabs WHERE id=?", (tab_id,))
    con.commit()
    con.close()
    return {"deleted": tab_id}


@app.get("/api/admin/users")
def get_users():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,username,email,full_name,role,is_active,is_locked FROM users")
    rows = cur.fetchall()
    con.close()
    return {
        "users": [
            {
                "id": r[0],
                "username": r[1],
                "email": r[2],
                "full_name": r[3],
                "role": r[4],
                "is_active": bool(r[5]),
                "is_locked": bool(r[6]),
            }
            for r in rows
        ],
    }


@app.post("/api/admin/users")
def create_user(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    hashed = hashlib.sha256((payload.get("password") or "changeme").encode()).hexdigest()
    cur.execute(
        "INSERT INTO users(username,email,full_name,hashed_password,role,is_active,is_locked) VALUES(?,?,?,?,?,?,?)",
        (
            payload["username"],
            payload.get("email"),
            payload.get("full_name"),
            hashed,
            payload.get("role", "user"),
            1 if payload.get("is_active", True) else 0,
            1 if payload.get("is_locked", False) else 0,
        ),
    )
    con.commit()
    con.close()
    return Response({"ok":True})


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sets = []
    args = []
    for field in ["username", "email", "full_name", "role"]:
        if field in payload:
            sets.append(f"{field}=?")
            args.append(payload[field])
    if "is_active" in payload:
        sets.append("is_active=?")
        args.append(1 if payload["is_active"] else 0)
    if "is_locked" in payload:
        sets.append("is_locked=?")
        args.append(1 if payload["is_locked"] else 0)
    if "password" in payload:
        sets.append("hashed_password=?")
        args.append(hashlib.sha256(payload["password"].encode()).hexdigest())
    args.append(user_id)
    cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", args)
    con.commit()
    con.close()
    return {"updated": user_id}


@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    con.commit()
    con.close()
    return {"deleted": user_id}


@app.get("/api/admin/roles")
def get_roles():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,name,slug,description,permissions FROM roles")
    rows = cur.fetchall()
    con.close()
    return {
        "roles": [
            {"id": r[0], "name": r[1], "slug": r[2], "description": r[3], "permissions": json.loads(r[4] or "{}")}
            for r in rows
        ],
    }


@app.post("/api/admin/roles")
def create_role(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO roles(name,slug,description,permissions) VALUES(?,?,?,?)",
        (
            payload["name"],
            payload["slug"],
            payload.get("description"),
            json.dumps(payload.get("permissions", {})),
        ),
    )
    con.commit()
    con.close()
    return Response({"ok":True})


@app.put("/api/admin/roles/{role_id}")
def update_role(role_id: int, payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sets = []
    args = []
    for field in ["name", "slug", "description"]:
        if field in payload:
            sets.append(f"{field}=?")
            args.append(payload[field])
    if "permissions" in payload:
        sets.append("permissions=?")
        args.append(json.dumps(payload["permissions"]))
    args.append(role_id)
    cur.execute(f"UPDATE roles SET {', '.join(sets)} WHERE id=?", args)
    con.commit()
    con.close()
    return {"updated": role_id}


@app.delete("/api/admin/roles/{role_id}")
def delete_role(role_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM roles WHERE id=?", (role_id,))
    con.commit()
    con.close()
    return {"deleted": role_id}


@app.get("/api/admin/notifications")
def get_notifications():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,platform,target,is_active,config_json FROM notifications")
    rows = cur.fetchall()
    con.close()
    return {
        "notifications": [
            {
                "id": r[0],
                "platform": r[1],
                "target": r[2],
                "is_active": bool(r[3]),
                "config": json.loads(r[4] or "{}"),
            }
            for r in rows
        ],
    }


@app.post("/api/admin/notifications")
def create_notification(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO notifications(platform,target,is_active,config_json) VALUES(?,?,?,?)",
        (
            payload["platform"],
            payload["target"],
            1 if payload.get("is_active", True) else 0,
            json.dumps(payload.get("config", {})),
        ),
    )
    con.commit()
    con.close()
    return Response({"ok":True})


@app.get("/api/admin/integrations")
def get_integrations():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,name,platform,base_url,is_active,config_json FROM integrations")
    rows = cur.fetchall()
    con.close()
    if not rows:
        return {
            "integrations": [
                {"name": "osTicket", "platform": "osticket", "base_url": "", "api_key": "", "is_active": False},
                {"name": "Zammad", "platform": "zammad", "base_url": "", "api_key": "", "is_active": False},
                {"name": "Email SMTP", "platform": "email", "base_url": "", "api_key": "", "is_active": False},
                {"name": "Telegram Bot", "platform": "telegram", "base_url": "", "api_key": "", "is_active": False},
                {"name": "Teams Webhook", "platform": "teams", "base_url": "", "api_key": "", "is_active": False},
                {"name": "PagerDuty", "platform": "pagerduty", "base_url": "", "api_key": "", "is_active": False},
                {"name": "Slack", "platform": "slack", "base_url": "", "api_key": "", "is_active": False},
                {"name": "OxiSDK", "platform": "oak", "base_url": "http://localhost:8000", "api_key": "", "is_active": False},
            ],
        }
    return {
        "integrations": [
            {
                "id": r[0],
                "name": r[1],
                "platform": r[2],
                "base_url": r[3],
                "api_key": (r[4] or "")[:8] + "...",
                "is_active": bool(r[4]),
                "config": json.loads(r[5] or "{}"),
            }
            for r in rows
        ],
    }


@app.post("/api/admin/integrations")
def create_integration(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO integrations(name,platform,base_url,api_key,is_active,config_json) VALUES(?,?,?,?,?,?)",
        (
            payload["name"],
            payload["platform"],
            payload.get("base_url", ""),
            payload.get("api_key", ""),
            1 if payload.get("is_active", False) else 0,
            json.dumps(payload.get("config", {})),
        ),
    )
    con.commit()
    con.close()
    return Response({"ok":True})


@app.put("/api/admin/integrations/{integration_id}")
def update_integration(integration_id: int, payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sets = []
    args = []
    for field in ["name", "platform", "base_url", "api_key"]:
        if field in payload:
            sets.append(f"{field}=?")
            args.append(payload[field])
    if "is_active" in payload:
        sets.append("is_active=?")
        args.append(1 if payload["is_active"] else 0)
    if "config" in payload:
        sets.append("config_json=?")
        args.append(json.dumps(payload["config"]))
    args.append(integration_id)
    cur.execute(f"UPDATE integrations SET {', '.join(sets)} WHERE id=?", args)
    con.commit()
    con.close()
    return {"updated": integration_id}


@app.delete("/api/admin/integrations/{integration_id}")
def delete_integration(integration_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM integrations WHERE id=?", (integration_id,))
    con.commit()
    con.close()
    return {"deleted": integration_id}


@app.get("/api/admin/setup/status")
def setup_status():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT value FROM app_state WHERE key='setup_complete'")
    row = cur.fetchone()
    cur.execute("SELECT count(*) FROM users")
    user_count = cur.fetchone()[0]
    con.close()
    # Check if setup is actually complete (value is 'true')
    setup_complete = False
    if row and row[0] == "true":
        setup_complete = True
    return {"configured": user_count > 0, "setup_complete": setup_complete, "users": user_count}


@app.post("/api/admin/setup/complete")
def setup_complete(payload: dict[str, Any]):
    """Mark setup as complete after admin changes default password"""
    password = payload.get("password")
    if not password or len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters"}
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    cur.execute("UPDATE users SET hashed_password=?, email=?, full_name=? WHERE username='admin'", 
                (hashed, payload.get("email"), payload.get("full_name", "Administrator")))
    cur.execute("INSERT OR REPLACE INTO app_state(key, value) VALUES('setup_complete', 'true')")
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/admin/setup/bootstrap")
def setup_bootstrap(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # create admin role
    cur.execute(
        "INSERT OR IGNORE INTO roles(name,slug,description,permissions) VALUES(?,?,?,?)",
        (
            "admin",
            "admin",
            "Platform administrator",
            json.dumps({"admin": True}),
        ),
    )
    con.commit()
    cur.execute("SELECT id FROM roles WHERE slug='admin'")
    role_id = cur.fetchone()[0]
    hashed = hashlib.sha256((payload.get("password") or "changeme").encode()).hexdigest()
    cur.execute(
        "INSERT INTO users(username,email,full_name,hashed_password,role) VALUES(?,?,?,?,?)",
        (
            payload.get("username", "admin"),
            payload.get("email"),
            payload.get("full_name", "Administrator"),
            hashed,
            "admin",
        ),
    )
    con.commit()
    con.close()
    return Response({"ok":True})


@app.get("/api/admin/policy")
def get_policy():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT key,value FROM app_state WHERE key='policy'")
    row = cur.fetchone()
    con.close()
    if row:
        return {"policy": json.loads(row[1])}
    return {
        "policy": {
            "password_min_length": 8,
            "session_timeout_minutes": 60,
            "max_login_attempts": 5,
            "require_2fa": False,
            "default_role": "user",
        },
    }


@app.put("/api/admin/policy")
def update_policy(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO app_state(key, value) VALUES(?,?)",
        ("policy", json.dumps(payload)),
    )
    con.commit()
    con.close()
    return {"updated": True}


@app.get("/api/admin/tenants/current")
def get_tenant():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT key,value FROM app_state WHERE key='tenant'")
    row = cur.fetchone()
    con.close()
    if row:
        return {"tenant": json.loads(row[1])}
    return {
        "tenant": {
            "name": "J1 NOC Platform",
            "logo_url": "/logo.png",
            "favicon_url": "/favicon.ico",
            "primary_color": "#1a73e8",
            "theme": "light",
        },
    }


@app.put("/api/admin/tenants/current")
def update_tenant(payload: dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO app_state(key, value) VALUES(?,?)",
        ("tenant", json.dumps(payload)),
    )
    con.commit()
    con.close()
    return {"updated": True}


# ─── Credential Management ────────────────────────────────────────────────

# Each entry carries `desc` (what it is / what to change) and `example`
# (a safe placeholder shown as prefill hint in the admin UI). `example` is
# NEVER persisted — it is only a UI hint when the field is empty.
CREDENTIAL_SCHEMA = [
    {"key": "POSTGRES_USER", "label": "PostgreSQL Username", "category": "database", "secret": False,
     "desc": "DB role the backend connects as. Must match the postgres container's POSTGRES_USER.", "example": "jnop"},
    {"key": "POSTGRES_PASSWORD", "label": "PostgreSQL Password", "category": "database", "secret": True,
     "desc": "Password for POSTGRES_USER. MUST match the postgres container's POSTGRES_PASSWORD or the backend gets 500s on every DB call (login, setup, admin tabs).", "example": "use-a-strong-random-value"},
    {"key": "POSTGRES_DB", "label": "PostgreSQL Database", "category": "database", "secret": False,
     "desc": "Database name. Must match POSTGRES_DB in the postgres container.", "example": "jnop"},
    {"key": "REDIS_PASSWORD", "label": "Redis Password", "category": "cache", "secret": True,
     "desc": "Redis AUTH password. Leave blank if Redis requires no password.", "example": "(empty)"},
    {"key": "SECRET_KEY", "label": "Application Secret Key", "category": "security", "secret": True,
     "desc": "JWT signing secret. Set to a long random string; rotating it invalidates all existing tokens.", "example": "run: openssl rand -hex 32"},
    {"key": "GRAFANA_ADMIN_PASSWORD", "label": "Grafana Admin Password", "category": "monitoring", "secret": True,
     "desc": "Admin password for the Grafana container (GF_SECURITY_ADMIN_PASSWORD).", "example": "admin"},
    {"key": "MITEL_SNMP_HOST", "label": "Mitel SNMP Host", "category": "telephony", "secret": False,
     "desc": "IP/hostname of the Mitel PBX to SNMP-poll. Use 'localhost' when polled from the host.", "example": "10.11.224.10"},
    {"key": "MITEL_SNMP_COMMUNITY", "label": "Mitel SNMP Community", "category": "telephony", "secret": True,
     "desc": "SNMP v2c community string for the PBX.", "example": "public"},
    {"key": "OSTICKET_BASE_URL", "label": "osTicket URL", "category": "helpdesk", "secret": False,
     "desc": "Base URL of osTicket (no trailing slash). Leave blank to use the built-in mock tickets.", "example": "https://helpdesk.example.com"},
    {"key": "OSTICKET_API_KEY", "label": "osTicket API Key", "category": "helpdesk", "secret": True,
     "desc": "osTicket REST API key (sent as X-API-Key). Required only when base URL is set.", "example": "paste-osTicket-api-key"},
    {"key": "LDAP_URL", "label": "LDAP Server URL", "category": "directory", "secret": False,
     "desc": "LDAP/AD server URI used for the Directory tab.", "example": "ldaps://ad.corp.local:636"},
    {"key": "LDAP_DOMAIN", "label": "LDAP Domain", "category": "directory", "secret": False,
     "desc": "NetBIOS/AD domain used for binds.", "example": "CORP"},
    {"key": "LDAP_BIND_DN", "label": "LDAP Bind DN", "category": "directory", "secret": False,
     "desc": "Distinguished name of the service account used to bind.", "example": "cn=svc-noc,ou=svc,dc=corp,dc=local"},
    {"key": "LDAP_BIND_PASSWORD", "label": "LDAP Bind Password", "category": "directory", "secret": True,
     "desc": "Password for the bind DN above.", "example": "bind-account-password"},
    {"key": "WAZUH_API_URL", "label": "Wazuh API URL", "category": "security", "secret": False,
     "desc": "Wazuh manager REST API base URL (used by the Wazuh SIEM tab).", "example": "https://wazuh.example.com:55000"},
    {"key": "WAZUH_USERNAME", "label": "Wazuh Username", "category": "security", "secret": False,
     "desc": "Wazuh API user.", "example": "wazuh"},
    {"key": "WAZUH_PASSWORD", "label": "Wazuh Password", "category": "security", "secret": True,
     "desc": "Wazuh API password.", "example": "wazuh"},
    {"key": "TELEGRAM_BOT_TOKEN", "label": "Telegram Bot Token", "category": "notifications", "secret": True,
     "desc": "Bot token from @BotFather used to push alerts to Telegram.", "example": "123456:ABC-DEF-..."},
    {"key": "TEAMS_WEBHOOK", "label": "Microsoft Teams Webhook", "category": "notifications", "secret": True,
     "desc": "Incoming webhook URL for Teams notifications.", "example": "https://outlook.office.com/webhook/..."},
    {"key": "NOTIFY_SMTP_HOST", "label": "SMTP Host", "category": "notifications", "secret": False,
     "desc": "SMTP relay host for email notifications.", "example": "smtp.example.com"},
    {"key": "NOTIFY_SMTP_USER", "label": "SMTP Username", "category": "notifications", "secret": False,
     "desc": "SMTP auth username (often a full email address).", "example": "noc@example.com"},
    {"key": "NOTIFY_SMTP_PASSWORD", "label": "SMTP Password", "category": "notifications", "secret": True,
     "desc": "SMTP auth password / app password.", "example": "smtp-app-password"},
]


@app.get("/api/admin/credentials/schema")
def get_credential_schema():
    """Return the credential schema (labels, categories, secret flags)."""
    return {"credentials": CREDENTIAL_SCHEMA}


@app.get("/api/admin/credentials")
def get_credentials():
    """Return all credential values (secrets masked)."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT key, value FROM app_state WHERE key LIKE 'cred_%'")
    rows = cur.fetchall()
    con.close()
    stored = {r[0][5:]: r[1] for r in rows}
    result = []
    for cred in CREDENTIAL_SCHEMA:
        k = cred["key"]
        val = stored.get(k, "")
        if val and cred["secret"]:
            decrypted = decrypt_value(val)
            display = decrypted[:4] + "••••" + decrypted[-4:] if len(decrypted) > 8 else "••••••••"
            result.append({**cred, "value": display, "has_value": bool(val)})
        else:
            result.append({**cred, "value": decrypt_value(val) if val else "", "has_value": bool(val)})
    return {"credentials": result}


@app.post("/api/admin/credentials")
def update_credentials(payload: dict[str, Any]):
    """Update one or more credential values."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    updated = []
    items = payload.get("credentials", [payload]) if isinstance(payload, dict) else payload
    for cred in items:
        key = cred.get("key")
        value = cred.get("value", "")
        if not key:
            continue
        schema_keys = {c["key"]: c for c in CREDENTIAL_SCHEMA}
        if key in schema_keys and schema_keys[key]["secret"]:
            encrypted = encrypt_value(value)
        else:
            encrypted = value
        cur.execute(
            "INSERT OR REPLACE INTO app_state(key, value) VALUES(?,?)",
            (f"cred_{key}", encrypted),
        )
        updated.append(key)
    con.commit()
    con.close()
    return {"updated": updated}


@app.get("/api/admin/credentials/export")
def export_credentials():
    """Export all credentials as a .env file content (for deploy script)."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT key, value FROM app_state WHERE key LIKE 'cred_%'")
    rows = cur.fetchall()
    con.close()
    lines = ["# J1 NOC Platform — Live Credentials", f"# Generated: {datetime.utcnow().isoformat()}", ""]
    for cred in CREDENTIAL_SCHEMA:
        k = cred["key"]
        stored = next((r[1] for r in rows if r[0] == f"cred_{k}"), "")
        if stored:
            val = decrypt_value(stored) if cred["secret"] else stored
            val = val.replace("'", "'\\''")
            lines.append(f"{k}={chr(39)}{val}{chr(39)}")
        else:
            lines.append(f"#{k}=")
    return Response(content="\n".join(lines), media_type="text/plain")


# ─── System Health ────────────────────────────────────────────────────────


@app.get("/api/admin/system/health")
def system_health():
    """Return system health info."""
    info = {
        "service": "admin-service",
        "version": "1.0.0",
        "status": "healthy",
        "uptime": datetime.utcnow().isoformat(),
        "docker": [],
    }
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                info["docker"].append({
                    "name": parts[0],
                    "status": parts[1],
                    "image": parts[2] if len(parts) > 2 else "",
                })
    except Exception:
        info["docker"] = [{"name": "error", "status": "cannot query Docker"}]
    return info


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)