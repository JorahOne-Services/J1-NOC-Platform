from fastapi import APIRouter

router = APIRouter()

@router.get("/ai/test")
def ai_test():
    return {"status": "ai works"}
