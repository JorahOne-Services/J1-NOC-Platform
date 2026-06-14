from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
import pathlib
router = APIRouter()
BASE = pathlib.Path('/srv/jnop/data')
@router.get('/dc_status')
def dc_status():
    p = BASE / 'dc_status.json'
    return JSONResponse(__import__('json').loads(p.read_text()) if p.exists() else [])
@router.get('/ntp_status')
def ntp_status():
    p = BASE / 'ntp_status.json'
    return JSONResponse(__import__('json').loads(p.read_text()) if p.exists() else {})
@router.get('/ntp_clients')
def ntp_clients():
    p = BASE / 'ntp_status.json'
    data = __import__('json').loads(p.read_text()) if p.exists() else {}
    clients = (data.get('clients') or data.get('ntp_clients') or [])
    return JSONResponse(clients)
@router.post('/dc/forcerepl')
async def force_repl(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})
