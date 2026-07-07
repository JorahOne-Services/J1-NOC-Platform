import os
import urllib.parse
from typing import Any

import requests
from app.config import get_settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

router = APIRouter()


def _wazuh_config():
    settings = get_settings()
    return {
        "url": getattr(
            settings, "wazuh_api_url", os.getenv("WAZUH_API_URL", "https://localhost:55000")
        ).rstrip("/"),
        "username": getattr(settings, "wazuh_username", os.getenv("WAZUH_USERNAME", "wazuh")),
        "password": getattr(settings, "wazuh_password", os.getenv("WAZUH_PASSWORD", "wazuh")),
        "verify_ssl": getattr(
            settings, "wazuh_verify_ssl", os.getenv("WAZUH_VERIFY_SSL", "false")
        ).lower()
        in ("1", "true", "yes"),
    }


OLLAMA_API_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _session(verify: bool = False) -> requests.Session:
    session = requests.Session()
    session.verify = verify
    retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def get_wazuh_token() -> str | None:
    """Get authentication token for Wazuh API"""
    cfg = _wazuh_config()
    try:
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.post(
                urllib.parse.urljoin(cfg["url"], "/security/user/authenticate"),
                auth=(cfg["username"], cfg["password"]),
                timeout=10,
            )
        if response.status_code == 200:
            return response.json()["data"]["token"]
        return None
    except Exception:
        return None


@router.get("/wazuh/status")
def get_wazuh_status():
    """Get Wazuh service status"""
    try:
        token = get_wazuh_token()
        if not token:
            return JSONResponse({"status": "Disconnected", "error": "Authentication failed"})

        headers = {"Authorization": f"Bearer {token}"}
        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.get(
                urllib.parse.urljoin(cfg["url"], "/manager/status"),
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            return JSONResponse({"status": "Connected", "data": response.json()})
        return JSONResponse(
            {"status": "Disconnected", "error": f"API returned {response.status_code}"}
        )
    except Exception as e:
        return JSONResponse({"status": "Disconnected", "error": str(e)})


@router.get("/wazuh/agents")
def get_wazuh_agents():
    """Get list of Wazuh agents"""
    try:
        token = get_wazuh_token()
        if not token:
            raise HTTPException(status_code=401, detail="Authentication failed")

        headers = {"Authorization": f"Bearer {token}"}
        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.get(
                urllib.parse.urljoin(cfg["url"], "/agents"),
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            return JSONResponse(response.json())
        raise HTTPException(
            status_code=response.status_code, detail=f"API returned {response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/wazuh/alerts")
def get_wazuh_alerts(limit: int = 50, offset: int = 0):
    """Get recent Wazuh alerts"""
    try:
        token = get_wazuh_token()
        if not token:
            raise HTTPException(status_code=401, detail="Authentication failed")

        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "limit": limit,
            "offset": offset,
            "sort": "-timestamp",
        }
        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.get(
                urllib.parse.urljoin(cfg["url"], "/alerts"),
                headers=headers,
                params=params,
                timeout=10,
            )

        if response.status_code == 200:
            return JSONResponse(response.json())
        raise HTTPException(
            status_code=response.status_code, detail=f"API returned {response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/wazuh/overview")
def get_wazuh_overview():
    """Get Wazuh system overview"""
    try:
        token = get_wazuh_token()
        if not token:
            raise HTTPException(status_code=401, detail="Authentication failed")

        headers = {"Authorization": f"Bearer {token}"}

        # Get manager info
        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            manager_response = session.get(
                urllib.parse.urljoin(cfg["url"], "/manager/info"),
                headers=headers,
                timeout=10,
            )

            # Get agents summary
            agents_response = session.get(
                urllib.parse.urljoin(cfg["url"], "/agents/summary/status"),
                headers=headers,
                timeout=10,
            )

            # Get alerts summary
            alerts_response = session.get(
                urllib.parse.urljoin(cfg["url"], "/overview/alerts"),
                headers=headers,
                timeout=10,
            )

        overview = {
            "manager": manager_response.json() if manager_response.status_code == 200 else {},
            "agents": agents_response.json() if agents_response.status_code == 200 else {},
            "alerts": alerts_response.json() if alerts_response.status_code == 200 else {},
        }

        return JSONResponse(overview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ollama/status")
def get_ollama_status():
    """Get Ollama service status"""
    try:
        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.get(
                urllib.parse.urljoin(OLLAMA_API_URL, "/api/tags"),
                timeout=10,
            )
        if response.status_code == 200:
            return JSONResponse(
                {"status": "Connected", "models": response.json().get("models", [])}
            )
        return JSONResponse(
            {"status": "Disconnected", "error": f"API returned {response.status_code}"}
        )
    except Exception as e:
        return JSONResponse({"status": "Disconnected", "error": str(e)})


@router.post("/ollama/chat")
def chat_with_ollama(payload: dict[str, Any]):
    """Chat with Ollama model"""
    try:
        model = payload.get("model", "llama3.2:1b")
        prompt = payload.get("prompt", "")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        cfg = _wazuh_config()
        with _session(verify=cfg["verify_ssl"]) as session:
            response = session.post(
                urllib.parse.urljoin(OLLAMA_API_URL, "/api/generate"),
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120,
            )

        if response.status_code == 200:
            return JSONResponse(response.json())
        raise HTTPException(
            status_code=response.status_code, detail=f"Ollama API returned {response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
