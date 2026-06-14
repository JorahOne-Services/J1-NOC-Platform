# Testing

## Backend
Run from repo root:
```bash
cd backend
source .venv/bin/activate
python -m pytest tests -q
```

## Frontend
```bash
cd frontend
npm install
npm run build
```

## Smoke
```bash
curl http://127.0.0.1:8000/healthz
```
