import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def get_token() -> str:
    r = client.post('/api/auth/login', data={'username': 'admin', 'password': 'admin'})
    assert r.status_code == 200
    return r.json()['access_token']


def test_overview_with_token():
    token = get_token()
    r = client.get('/api/dashboard/overview', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    data = r.json()
    assert 'clients_online' in data
    assert 'alerts' in data
