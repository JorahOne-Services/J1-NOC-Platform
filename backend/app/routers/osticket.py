from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import os
import httpx

router = APIRouter()

OSTICKET_BASE = os.getenv("OSTICKET_BASE_URL", "").rstrip("/")
OSTICKET_KEY = os.getenv("OSTICKET_API_KEY", "")

if not OSTICKET_BASE or not OSTICKET_KEY:
    # Allow the router to load even without creds; endpoints will 503 until configured
    pass

HEADERS = {"X-API-Key": OSTICKET_KEY} if OSTICKET_KEY else {}


@router.get("/helpdesk/tickets")
async def list_tickets(request: Request):
    if not OSTICKET_BASE:
        raise HTTPException(status_code=503, detail="osTicket not configured")
    params = dict(request.query_params)
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{OSTICKET_BASE}/api/http.php/tickets.json", headers=HEADERS, params=params)
    return JSONResponse(r.json(), status_code=r.status_code)


@router.get("/helpdesk/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    if not OSTICKET_BASE:
        raise HTTPException(status_code=503, detail="osTicket not configured")
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{OSTICKET_BASE}/api/http.php/tickets/{ticket_id}.json", headers=HEADERS)
    return JSONResponse(r.json(), status_code=r.status_code)


@router.post("/helpdesk/tickets")
async def create_ticket(request: Request):
    if not OSTICKET_BASE:
        raise HTTPException(status_code=503, detail="osTicket not configured")
    body = await request.json()
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{OSTICKET_BASE}/api/http.php/tickets.json", headers=HEADERS, json=body)
    return JSONResponse(r.json(), status_code=r.status_code)
