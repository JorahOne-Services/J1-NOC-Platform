from fastapi import APIRouter
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/status")
def status():
    return {"nocs": 3, "alerts": 0, "uptime": "100%"}
