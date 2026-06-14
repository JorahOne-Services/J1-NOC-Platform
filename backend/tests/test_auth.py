import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get('/healthz')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_login_returns_token():
    r = client.post('/api/auth/login', data={'username': 'admin', 'password': 'admin'})
    assert r.status_code == 200
    body = r.json()
    assert body['token_type'] == 'bearer'
    assert isinstance(body['access_token'], str)
    assert len(body['access_token']) > 10


def test_dashboard_requires_auth():
    r = client.get('/api/dashboard/overview')
    assert r.status_code == 401
