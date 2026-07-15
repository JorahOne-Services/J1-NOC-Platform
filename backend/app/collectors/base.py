"""Secret-safe collector base utilities.

J1 NOC secret policy (enforced here):
- Credentials are read ONLY from the encrypted DB vault (``config.get_db_setting``)
  or the injected host environment. Never hardcoded, never from the repo.
- Raw credential values are NEVER written to disk or logs. Use ``mask()``.
- Collector output JSON lives ONLY under ``/srv/jnop/data`` (outside the repo).
- Every collector swallows its own exceptions and records status; it must never
  raise into the scheduler.
"""

from __future__ import annotations

import json
import logging
import pathlib
from datetime import UTC, datetime

from .. import config

logger = logging.getLogger("jnop.collectors")

# Output root lives on the host, outside the git repo. Overridable for tests.
DATA_DIR = pathlib.Path("/srv/jnop/data")
STATUS_FILE = "collector_status.json"


def get_cred(key: str, default: str = "") -> str:
    """Read a credential/setting from the encrypted vault (DB) only."""
    try:
        return config.get_db_setting(key, default)
    except Exception:
        return default


def mask(value) -> str:
    """Mask a secret for logs: show only last 4 chars, never the full value."""
    if not value:
        return "<unset>"
    s = str(value)
    if len(s) <= 4:
        return "****"
    return "****" + s[-4:]


def write_json(name: str, data) -> None:
    """Atomically write operational JSON to the data dir (never a secret)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def record_status(name: str, ok: bool, detail: str = "") -> None:
    """Record a collector run result into the shared status file."""
    try:
        try:
            existing = json.loads((DATA_DIR / STATUS_FILE).read_text())
        except Exception:
            existing = []
        if not isinstance(existing, list):
            existing = []
        existing = [s for s in existing if isinstance(s, dict) and s.get("name") != name]
        existing.append(
            {
                "name": name,
                "ok": ok,
                "detail": detail,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        write_json(STATUS_FILE, existing)
    except Exception:
        pass
