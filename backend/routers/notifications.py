from fastapi import APIRouter
router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/preferences")
def preferences():
    return {"email": True, "telegram": False, "webhook": True}
