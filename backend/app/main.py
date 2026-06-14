from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import engine, Base
from .routers import health, auth, dashboard, notifications, tools, ai, static_data, osticket


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="J1 NOC Platform",
        version="0.2.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", include_in_schema=False)
    def healthz_root():
        return {"status": "ok"}

    @app.post("/forcerepl", include_in_schema=False)
    async def forcerepl_root(request: Request):
        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes.decode() if body_bytes else "{}")
        except Exception as exc:
            return JSONResponse({"Success": False, "Error": str(exc)}, status_code=200)
        return JSONResponse({"Success": True, "Request": body})

    app.include_router(static_data.router, prefix="/api")
    app.include_router(health.router)
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(osticket.router, prefix="/api")

    return app


app = create_app()
