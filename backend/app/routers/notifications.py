from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/notifications/test")
def test_notifications():
    return JSONResponse({"ok": True, "status": "notifications router reachable"})


@router.post("/notifications/send")
def send_notification(payload: dict):
    return {"ok": True}
