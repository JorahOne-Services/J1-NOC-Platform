import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import routers as _routers
from .config import get_settings
from .logging_config import configure_logging
from .routers import (
    ai,
    auth,
    dashboard,
    health,
    metrics,
    notifications,
    setup,
    static_data,
    system,
    tools,
    wazuh,
)
from .routers import osticket as helpdesk

try:  # optional, missing in some environments
    from .routers import admin as _admin
    from .routers import settings as _settings
except Exception:  # pragma: no cover - degrade gracefully
    _admin = None
    _settings = None

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed exclusively via Alembic migrations (no create_all in app).
    # Run `alembic upgrade head` out-of-band or via the deploy script.
    yield


async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path
    from .routers.metrics import HTTP_REQUEST_COUNT, HTTP_REQUEST_LATENCY

    HTTP_REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    HTTP_REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
    return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="J1 NOC Platform",
        version="11.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(prometheus_middleware)

    @app.get("/healthz", include_in_schema=False)
    def healthz_root() -> dict:
        return {"status": "ok"}

    @app.post("/forcerepl", include_in_schema=False)
    async def forcerepl_root(request: Request) -> JSONResponse:
        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes.decode() if body_bytes else "{}")
        except Exception as exc:
            logger.exception("Invalid JSON payload received on /forcerepl", exc_info=exc)
            return JSONResponse(
                {"Success": False, "Error": "Invalid request payload"}, status_code=200
            )
        return JSONResponse({"Success": True, "Request": body})

    app.include_router(static_data.router, prefix="/api")
    app.include_router(metrics.router)
    app.include_router(system.router, prefix="/api")

    app.include_router(health.router)
    app.include_router(health.router, prefix="/api")

    app.include_router(setup.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(wazuh.router, prefix="/api")

    if getattr(_routers, "agent", None) is not None:
        import app.routers.agent as _agent  # type: ignore[import-not-found]

        if hasattr(_agent, "router"):
            app.include_router(_agent.router, prefix="/api")

    app.include_router(helpdesk.router, prefix="/api")

    if _admin is not None:
        app.include_router(_admin.router, prefix="/api")

    if _settings is not None:
        app.include_router(_settings.router, prefix="/api")

    return app


app = create_app()
