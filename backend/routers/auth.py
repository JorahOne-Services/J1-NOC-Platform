from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginRequest):
    if payload.username == "admin" and payload.password == "admin":
        return {"access_token": "demo", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="invalid credentials")
