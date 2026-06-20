from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.db.redis import get_redis_client
from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.health import HealthPayload, ReadinessDetails
from app.services.health_service import build_live_response

router = APIRouter()
SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.get("/live", response_model=ApiResponse[HealthPayload])
async def liveness(request: Request, settings: SettingsDep) -> ApiResponse[HealthPayload]:
    data = build_live_response(service=settings.app_name, environment=settings.app_env)
    return success_response(data, request)


@router.get("/ready", response_model=ApiResponse[HealthPayload])
def readiness(
    request: Request,
    db: SessionDep,
    settings: SettingsDep,
) -> ApiResponse[HealthPayload]:
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except SQLAlchemyError:
        database_status = "unavailable"

    redis_status = "ok"
    redis_client = get_redis_client()
    if redis_client is None:
        redis_status = "degraded"
    else:
        try:
            redis_client.ping()
        except Exception:
            redis_status = "degraded"

    status = "ok" if (database_status == "ok" and redis_status == "ok") else "degraded"

    return success_response(
        HealthPayload(
        status=status,
        service=settings.app_name,
        environment=settings.app_env,
        details=ReadinessDetails(database=database_status, redis=redis_status),
        ),
        request,
    )
