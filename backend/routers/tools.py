from fastapi import APIRouter
router = APIRouter(prefix="/tools", tags=["tools"])

@router.get("/ping")
def ping(target: str | None = None):
    return {"tool": "ping", "target": target or "127.0.0.1", "alive": True}
