"""Expose collector run status to the dashboard (no secrets)."""
from __future__ import annotations

import json

from fastapi import APIRouter

from ..collectors.base import DATA_DIR, STATUS_FILE

router = APIRouter()


@router.get("/integrations/status")
def integrations_status():
    try:
        return json.loads((DATA_DIR / STATUS_FILE).read_text())
    except Exception:
        return []
