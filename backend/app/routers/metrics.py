"""Prometheus metrics endpoint for the J1 NOC Platform backend.

Exposes process and app-level metrics at /metrics for scraping by Prometheus.
"""

from contextlib import suppress

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector

router = APIRouter()

HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)
DB_CONNECTED = Gauge(
    "db_connected",
    "1 if the database is reachable, else 0",
)


@router.get("/metrics", include_in_schema=False)
def metrics(request: Request) -> Response:
    # Support multi-process deployments (gunicorn/uvicorn workers)
    from prometheus_client import REGISTRY

    with suppress(Exception):
        MultiProcessCollector(REGISTRY)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
