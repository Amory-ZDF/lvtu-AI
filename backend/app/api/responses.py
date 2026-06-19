from datetime import UTC, datetime
from typing import Any

from fastapi import Request

from app.schemas.common import ApiError, ApiErrorResponse, ApiResponse, ResponseMeta


def build_meta(
    request: Request | None = None,
    *,
    provider: str | None = None,
    warnings: list[str] | None = None,
    page: int | None = None,
    page_size: int | None = None,
    total: int | None = None,
    has_more: bool | None = None,
) -> ResponseMeta:
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)

    return ResponseMeta(
        request_id=request_id,
        timestamp=datetime.now(UTC),
        provider=provider,
        warnings=warnings or [],
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


def success_response(
    data: Any,
    request: Request | None = None,
    *,
    provider: str | None = None,
    warnings: list[str] | None = None,
) -> ApiResponse[Any]:
    return ApiResponse[Any](
        data=data,
        meta=build_meta(request, provider=provider, warnings=warnings),
    )


def paginated_response(
    items: Any,
    request: Request | None = None,
    *,
    page: int,
    page_size: int,
    total: int,
    provider: str | None = None,
    warnings: list[str] | None = None,
) -> ApiResponse[Any]:
    """构建分页响应，data 为 {"items": [...], "meta": {...}}，meta 同时置于 data 内便于前端解包。"""
    has_more = page * page_size < total
    pagination_meta = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": has_more,
    }
    meta = build_meta(
        request,
        provider=provider,
        warnings=warnings,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )
    return ApiResponse[Any](data={"items": items, "meta": pagination_meta}, meta=meta)


def error_response(
    *,
    code: str,
    message: str,
    request: Request | None = None,
    details: list[Any] | None = None,
) -> ApiErrorResponse:
    return ApiErrorResponse(
        error=ApiError(code=code, message=message, details=details or []),
        meta=build_meta(request),
    )
