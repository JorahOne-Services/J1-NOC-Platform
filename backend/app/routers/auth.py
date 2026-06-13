from fastapi import APIRouter

router = APIRouter()

@router.get("/auth/test")
def auth_test():
    return {"status": "auth works"}
