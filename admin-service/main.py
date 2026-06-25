from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta

DB_PATH = "/srv/jnop/admin-service/admin.sqlite"

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
        """
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
    return JSONResponse({"ok":True})


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
        ]
    }


@app.post("/api/admin/tabs")
def create_tab(payload: Dict[str, Any]):
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
def update_tab(tab_id: int, payload: Dict[str, Any]):
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
        ]
    }


@app.post("/api/admin/users")
def create_user(payload: Dict[str, Any]):
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
    return JSONResponse({"ok":True})


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, payload: Dict[str, Any]):
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
        ]
    }


@app.post("/api/admin/roles")
def create_role(payload: Dict[str, Any]):
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
    return JSONResponse({"ok":True})


@app.put("/api/admin/roles/{role_id}")
def update_role(role_id: int, payload: Dict[str, Any]):
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
        ]
    }


@app.post("/api/admin/notifications")
def create_notification(payload: Dict[str, Any]):
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
    return JSONResponse({"ok":True})


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
            ]
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
        ]
    }


@app.post("/api/admin/integrations")
def create_integration(payload: Dict[str, Any]):
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
    return JSONResponse({"ok":True})


@app.put("/api/admin/integrations/{integration_id}")
def update_integration(integration_id: int, payload: Dict[str, Any]):
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
    cur.execute("SELECT count(*) FROM users")
    count = cur.fetchone()[0]
    con.close()
    return {"configured": count > 0, "users": count}


@app.post("/api/admin/setup/bootstrap")
def setup_bootstrap(payload: Dict[str, Any]):
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
    return JSONResponse({"ok":True})


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
        }
    }


@app.put("/api/admin/policy")
def update_policy(payload: Dict[str, Any]):
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
        }
    }


@app.put("/api/admin/tenants/current")
def update_tenant(payload: Dict[str, Any]):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO app_state(key, value) VALUES(?,?)",
        ("tenant", json.dumps(payload)),
    )
    con.commit()
    con.close()
    return {"updated": True}
