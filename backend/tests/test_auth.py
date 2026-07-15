import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://localhost","http://127.0.0.1"]')

from app.database import Base, engine
from app.main import app
from app.models import Role, User
from app.routers.auth import get_password_hash
from fastapi.testclient import TestClient

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def seed_admin():
    from app.database import SessionLocal
    from sqlalchemy.orm import Session

    db: Session = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Super Admin").first()
        if role is None:
            role = Role(name="Super Admin", slug="super-admin", is_system=True)
            db.add(role)
            db.commit()
            db.refresh(role)
        if db.query(User).filter(User.username == "admin").first() is None:
            db.add(
                User(
                    username="admin",
                    email="admin@local",
                    full_name="Admin",
                    hashed_password=get_password_hash("admin"),
                    role_id=role.id,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_returns_token():
    seed_admin()
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 10


def test_dashboard_requires_auth():
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 401
