from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import engine, Base
from .routers import health, auth, dashboard, notifications, tools, ai


settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="J1 NOC Platform",
        version="0.2.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")

    return app


app = create_app()
