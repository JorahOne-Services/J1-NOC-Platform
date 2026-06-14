from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard/overview")
def dashboard_overview():
    return {"clients_online": 0, "alerts": 0, "score": 100}
