from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.integrations.amap.client import get_amap_client
from app.schemas.common import ApiResponse
from app.schemas.planning import (
    DestinationRecommendationPayload,
    DestinationRecommendationRequest,
    DestinationWeatherPayload,
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


@router.get("/weather", response_model=ApiResponse[DestinationWeatherPayload])
def destination_weather(
    request: Request,
    destination_name: str = Query(..., min_length=1, max_length=80),
) -> ApiResponse[DestinationWeatherPayload]:
    client = get_amap_client()
    if not client.available:
        data = DestinationWeatherPayload(
            destination_name=destination_name,
            available=False,
            message="当前环境未配置高德 Web 服务 Key，出发前请手动复核目的地天气。",
        )
        return success_response(data, request, provider="amap")

    try:
        geocode = client.geocode(destination_name)
        city = (geocode.get("city") or geocode.get("province")) if geocode else None
        adcode = geocode.get("adcode") if geocode else None
        weather = client.weather_live(adcode or destination_name)
    except Exception:
        data = DestinationWeatherPayload(
            destination_name=destination_name,
            available=False,
            message="天气服务暂时不可用，建议出发前一天再次复核。",
        )
        return success_response(data, request, provider="amap")

    if not weather:
        data = DestinationWeatherPayload(
            destination_name=destination_name,
            available=False,
            city=city,
            adcode=adcode,
            message="暂未获取到实时天气，建议出发前一天再次复核。",
        )
        return success_response(data, request, provider="amap")

    data = DestinationWeatherPayload(
        destination_name=destination_name,
        available=True,
        city=weather.get("city") or city,
        adcode=weather.get("adcode") or adcode,
        weather=weather.get("weather"),
        temperature=weather.get("temperature"),
        wind_direction=weather.get("winddirection"),
        wind_power=weather.get("windpower"),
        humidity=weather.get("humidity"),
        report_time=weather.get("reporttime"),
    )
    return success_response(data, request, provider="amap")


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
