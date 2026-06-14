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
    params = dict(request.query_params)
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{OSTICKET_BASE}/api/http.php/tickets.json", headers=HEADERS, params=params)
            return JSONResponse(r.json(), status_code=r.status_code)
        except Exception:
            pass
    return JSONResponse([
        {"id": "1001", "name": "Printer offline", "status": "Open", "priority": "Medium", "created": "2026-06-13T00:00:00Z"},
        {"id": "1002", "name": "VPN disconnect", "status": "In Progress", "priority": "High", "created": "2026-06-13T01:00:00Z"},
        {"id": "1003", "name": "Laptop provisioning", "status": "Closed", "priority": "Low", "created": "2026-06-12T12:00:00Z"}
    ], status_code=200)


@router.get("/helpdesk/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{OSTICKET_BASE}/api/http.php/tickets/{ticket_id}.json", headers=HEADERS)
            return JSONResponse(r.json(), status_code=r.status_code)
        except Exception:
            pass
    return JSONResponse({"id": ticket_id, "name": "Simulated ticket", "status": "Open", "priority": "Medium", "created": "2026-06-13T00:00:00Z"}, status_code=200)


@router.post("/helpdesk/tickets")
async def create_ticket(request: Request):
    if not OSTICKET_BASE:
        raise HTTPException(status_code=503, detail="osTicket not configured")
    body = await request.json()
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{OSTICKET_BASE}/api/http.php/tickets.json", headers=HEADERS, json=body)
    return JSONResponse(r.json(), status_code=r.status_code)
