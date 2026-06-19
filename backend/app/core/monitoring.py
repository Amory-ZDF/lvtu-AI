"""Prometheus monitoring instrumentation.

This module provides optional Prometheus metrics for the FastAPI application.
``prometheus_client`` is an OPTIONAL dependency: if it is not installed, all
public helpers degrade to no-ops so the application keeps running unchanged.

Exposed metrics (when available):
    - http_requests_total{method, path, status}
    - http_request_duration_seconds{method, path} (histogram)
    - http_errors_total{method, path, status}

Usage in ``app.main.py``::

    from app.core.monitoring import register_metrics

    register_metrics(app)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("app.monitoring")

try:  # pragma: no cover - optional dependency
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )

    _PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _DummyMetric:
        """No-op stand-in used when prometheus_client is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        def labels(self, *args: Any, **kwargs: Any) -> "_DummyMetric":
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:
            return None

        def observe(self, *args: Any, **kwargs: Any) -> None:
            return None

    def generate_latest() -> bytes:  # type: ignore[no-redef]
        return b""

    Counter = _DummyMetric  # type: ignore[assignment, misc]
    Histogram = _DummyMetric  # type: ignore[assignment, misc]


# ---------------------------------------------------------------------------
# Metric definitions (no-ops when prometheus_client is missing)
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests handled.",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total number of HTTP requests that returned an error status (>=400).",
    ["method", "path", "status"],
)


def is_metrics_enabled() -> bool:
    """Return True when prometheus_client is importable."""
    return _PROMETHEUS_AVAILABLE


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request count, latency, and error count for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Skip recording the metrics endpoint itself to avoid feedback loops.
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            method = request.method
            path = request.url.path
            status = str(status_code)

            try:
                REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
                REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
                if status_code >= 400:
                    ERROR_COUNT.labels(method=method, path=path, status=status).inc()
            except Exception:  # pragma: no cover - defensive
                logger.debug("Failed to record metrics", exc_info=True)


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def metrics_endpoint() -> Response:
    """Return the latest Prometheus metrics payload."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def register_metrics(app: "FastAPI") -> None:
    """Register the metrics middleware and ``/metrics`` route.

    Safe to call even when ``prometheus_client`` is not installed — in that
    case the middleware becomes a thin pass-through and ``/metrics`` returns
    an empty body, so the application behaves identically.
    """

    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", tags=["monitoring"], include_in_schema=_PROMETHEUS_AVAILABLE)
    async def _metrics() -> Response:  # pragma: no cover - thin wrapper
        return metrics_endpoint()

    if _PROMETHEUS_AVAILABLE:
        logger.info("Prometheus metrics enabled at /metrics")
    else:
        logger.info("prometheus_client not installed; metrics instrumentation disabled")
