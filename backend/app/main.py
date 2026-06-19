from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.responses import success_response
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.monitoring import register_metrics
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.ai_quota import AIQuotaMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(AIQuotaMiddleware, settings=settings)
app.add_middleware(RateLimitMiddleware, settings=settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)
register_exception_handlers(app)
register_metrics(app)


@app.get("/", tags=["root"])
async def root(request: Request):
    return success_response(
        {
            "service": settings.app_name,
            "environment": settings.app_env,
            "message": f"{settings.app_name} is running",
        },
        request,
    )
