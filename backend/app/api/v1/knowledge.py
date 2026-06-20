"""知识库搜索 API：支持本地 DB 搜索 + 高德 API 实时搜索。"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.responses import success_response
from app.db.session import get_db_session
from app.integrations.amap import get_amap_client
from app.models.destination import Destination
from app.models.outfit import Outfit
from app.models.photo_spot import PhotoSpot
from app.schemas.common import ApiResponse

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]


# --------------------------------------------------------------------------- #
# 目的地知识库
# --------------------------------------------------------------------------- #

@router.get("/destinations", tags=["knowledge"])
def list_destinations(
    request: Request,
    db: SessionDep,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    country: str | None = Query(default=None, description="国家/地区筛选"),
    tag: str | None = Query(default=None, description="氛围标签筛选"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    stmt = select(Destination)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Destination.name.ilike(pattern),
                Destination.description.ilike(pattern),
                Destination.country_or_region.ilike(pattern),
            )
        )
    if country:
        stmt = stmt.where(Destination.country_or_region == country)
    if tag:
        stmt = stmt.where(Destination.vibe_tags.contains([tag]))

    total = len(list(db.scalars(stmt)))
    stmt = stmt.order_by(Destination.popularity.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt))

    return success_response(
        {
            "items": [_destination_to_dict(d) for d in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        request,
    )


@router.get("/destinations/{destination_id}", tags=["knowledge"])
def get_destination(
    request: Request,
    db: SessionDep,
    destination_id: str,
) -> ApiResponse:
    dest = db.get(Destination, destination_id)
    if not dest:
        return success_response(None, request, message="目的地不存在")
    return success_response(_destination_to_dict(dest), request)


# --------------------------------------------------------------------------- #
# 机位知识库
# --------------------------------------------------------------------------- #

@router.get("/photo-spots", tags=["knowledge"])
def list_photo_spots(
    request: Request,
    db: SessionDep,
    keyword: str | None = Query(default=None),
    destination: str | None = Query(default=None, description="按目的地筛选"),
    min_score: float | None = Query(default=None, ge=0, le=10),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    stmt = select(PhotoSpot)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                PhotoSpot.name.ilike(pattern),
                PhotoSpot.location.ilike(pattern),
                PhotoSpot.description.ilike(pattern),
            )
        )
    if destination:
        stmt = stmt.where(PhotoSpot.destination_name == destination)
    if min_score is not None:
        stmt = stmt.where(PhotoSpot.photo_score >= min_score)

    total = len(list(db.scalars(stmt)))
    stmt = stmt.order_by(PhotoSpot.photo_score.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt))

    return success_response(
        {
            "items": [_photo_spot_to_dict(s) for s in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        request,
    )


# --------------------------------------------------------------------------- #
# 穿搭知识库
# --------------------------------------------------------------------------- #

@router.get("/outfits", tags=["knowledge"])
def list_outfits(
    request: Request,
    db: SessionDep,
    destination: str | None = Query(default=None),
    season: str | None = Query(default=None),
    scene: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    stmt = select(Outfit)
    if destination:
        stmt = stmt.where(Outfit.destination_name == destination)
    if season:
        stmt = stmt.where(Outfit.season == season)
    if scene:
        stmt = stmt.where(Outfit.scene == scene)

    total = len(list(db.scalars(stmt)))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt))

    return success_response(
        {
            "items": [_outfit_to_dict(o) for o in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        request,
    )


# --------------------------------------------------------------------------- #
# 高德 API 实时搜索
# --------------------------------------------------------------------------- #

@router.get("/amap/pois", tags=["knowledge"])
def amap_search_pois(
    request: Request,
    keywords: str = Query(..., description="搜索关键词，如 '故宫'"),
    city: str | None = Query(default=None, description="城市名，如 '北京'"),
    types: str | None = Query(default=None, description="POI 类型码，如 '110000' 风景名胜"),
    page_size: int = Query(default=20, ge=1, le=25),
) -> ApiResponse:
    client = get_amap_client()
    if not client.available:
        return success_response(
            {"items": [], "available": False, "message": "AMAP_API_KEY 未配置"},
            request,
        )
    pois = client.search_pois(keywords=keywords, city=city, types=types, page_size=page_size)
    return success_response(
        {"items": pois, "available": True, "count": len(pois)},
        request,
    )


@router.get("/amap/around", tags=["knowledge"])
def amap_search_around(
    request: Request,
    location: str = Query(..., description="中心坐标 '经度,纬度'，如 '116.397428,39.90923'"),
    keywords: str | None = Query(default=None),
    types: str | None = Query(default=None),
    radius: int = Query(default=3000, ge=1, le=50000, description="搜索半径（米）"),
) -> ApiResponse:
    client = get_amap_client()
    if not client.available:
        return success_response(
            {"items": [], "available": False, "message": "AMAP_API_KEY 未配置"},
            request,
        )
    pois = client.search_around(
        location=location, keywords=keywords, types=types, radius=radius
    )
    return success_response(
        {"items": pois, "available": True, "count": len(pois)},
        request,
    )


# --------------------------------------------------------------------------- #
# 序列化辅助
# --------------------------------------------------------------------------- #

def _destination_to_dict(d: Destination) -> dict[str, Any]:
    return {
        "id": str(d.id),
        "name": d.name,
        "country_or_region": d.country_or_region,
        "description": d.description,
        "best_season": d.best_season,
        "budget_range": d.budget_range,
        "vibe_tags": d.vibe_tags,
        "highlights": d.highlights,
        "climate": d.climate,
        "language": d.language,
        "currency": d.currency,
        "timezone": d.timezone,
        "latitude": float(d.latitude) if d.latitude is not None else None,
        "longitude": float(d.longitude) if d.longitude is not None else None,
        "hero_image_url": d.hero_image_url,
        "gallery": d.gallery,
        "average_days": d.average_days,
        "popularity": d.popularity,
        "reasons": d.reasons,
    }


def _photo_spot_to_dict(s: PhotoSpot) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "name": s.name,
        "destination_name": s.destination_name,
        "location": s.location,
        "description": s.description,
        "composition": s.composition,
        "best_time": s.best_time,
        "best_season": s.best_season,
        "photo_score": s.photo_score,
        "tips": s.tips,
        "equipment": s.equipment,
        "latitude": float(s.latitude) if s.latitude is not None else None,
        "longitude": float(s.longitude) if s.longitude is not None else None,
        "tags": s.tags,
        "images": s.images,
    }


def _outfit_to_dict(o: Outfit) -> dict[str, Any]:
    return {
        "id": str(o.id),
        "destination_name": o.destination_name,
        "season": o.season,
        "scene": o.scene,
        "style": o.style,
        "items": o.items,
        "tips": o.tips,
        "weather_note": o.weather_note,
        "images": o.images,
    }
