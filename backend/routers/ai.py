from fastapi import APIRouter
router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/assistant")
def assistant(q: str | None = None):
    return {"reply": f"AI echo: {q or ''}"}
