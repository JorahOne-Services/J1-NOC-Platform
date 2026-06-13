from fastapi import APIRouter

router = APIRouter()

@router.get("/tools/test")
def tools_test():
    return {"status": "tools works"}
