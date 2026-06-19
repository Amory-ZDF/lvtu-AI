from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.planning import (
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    MediaPlaceholderPayload,
    MediaPlaceholderRequest,
    RouteGenerationPayload,
    RouteGenerationRequest,
)
from app.services.job_service import complete_job, create_job
from app.services.planning_service import (
    get_destination_recommendations,
    get_media_placeholders,
    get_route_generation,
)

router = APIRouter()
SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.post("/destinations", response_model=ApiResponse[DestinationRecommendationPayload])
def recommend_destinations(
    payload: DestinationRecommendationRequest,
    request: Request,
    settings: SettingsDep,
) -> ApiResponse[DestinationRecommendationPayload]:
    data, provider = get_destination_recommendations(payload, settings)
    return success_response(data, request, provider=provider)


@router.post("/routes", response_model=ApiResponse[RouteGenerationPayload])
def generate_routes(
    payload: RouteGenerationRequest,
    request: Request,
    settings: SettingsDep,
) -> ApiResponse[RouteGenerationPayload]:
    data, provider = get_route_generation(payload, settings)
    return success_response(data, request, provider=provider)


@router.post("/media/placeholders", response_model=ApiResponse[MediaPlaceholderPayload])
def placeholder_media(
    payload: MediaPlaceholderRequest,
    request: Request,
    settings: SettingsDep,
) -> ApiResponse[MediaPlaceholderPayload]:
    data, provider = get_media_placeholders(payload, settings)
    return success_response(data, request, provider=provider)


@router.post("/destinations/async", tags=["planning"])
def recommend_destinations_async(
    payload: DestinationRecommendationRequest,
    request: Request,
    settings: SettingsDep,
    db: SessionDep,
) -> ApiResponse:
    """异步目的地推荐：创建生成任务，当前用 mock 立即完成 job。

    返回 `{job_id, status}`，客户端可通过 `GET /jobs/{job_id}` 获取结果。
    """
    job = create_job(
        db,
        "destination_recommendation",
        None,
        payload.model_dump(mode="json"),
    )
    data, provider = get_destination_recommendations(payload, settings)
    job = complete_job(db, job.job_id, data.model_dump(mode="json"))
    return success_response(
        {"job_id": job.job_id, "status": job.status, "output_data": job.output_data},
        request,
        provider=provider,
    )


@router.post("/routes/async", tags=["planning"])
def generate_routes_async(
    payload: RouteGenerationRequest,
    request: Request,
    settings: SettingsDep,
    db: SessionDep,
) -> ApiResponse:
    """异步路线生成：创建生成任务，当前用 mock 立即完成 job。

    返回 `{job_id, status}`，客户端可通过 `GET /jobs/{job_id}` 获取结果。
    """
    job = create_job(
        db,
        "route_generation",
        None,
        payload.model_dump(mode="json"),
    )
    data, provider = get_route_generation(payload, settings)
    job = complete_job(db, job.job_id, data.model_dump(mode="json"))
    return success_response(
        {"job_id": job.job_id, "status": job.status, "output_data": job.output_data},
        request,
        provider=provider,
    )
