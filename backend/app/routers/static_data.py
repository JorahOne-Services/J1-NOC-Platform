from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json
import pathlib

router = APIRouter()
BASE = pathlib.Path('/srv/jnop/data')


@router.get('/dc_status')
def dc_status():
    p = BASE / 'dc_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        data = payload.get('DCs') or payload.get('dc_status') or []
    elif isinstance(payload, list):
        data = payload
    else:
        data = []
    return JSONResponse(data)


@router.get('/ntp_status')
def ntp_status():
    p = BASE / 'ntp_status.json'
    try:
        payload = json.loads(p.read_text())
    except Exception:
        payload = {}
    return JSONResponse(payload or {})


@router.get('/ntp_clients')
def ntp_clients():
    p = BASE / 'ntp_status.json'
    data = {}
    try:
        data = json.loads(p.read_text()) or {}
    except Exception:
        data = {}
    clients = data.get('Clients') or data.get('clients') or data.get('ntp_clients') or []
    return JSONResponse(clients)


@router.post('/dc/forcerepl')
async def force_repl(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})


@router.get('/tags')
def tags():
    return JSONResponse([])


@router.post('/generate')
async def generate(request: Request):
    body = await request.json()
    return JSONResponse({'Success': True, 'Request': body})
