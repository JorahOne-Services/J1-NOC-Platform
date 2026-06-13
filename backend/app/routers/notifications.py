from fastapi import APIRouter

router = APIRouter()

@router.get("/notifications/test")
def notifications_test():
    return {"status": "notifications works"}
