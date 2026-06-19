from __future__ import annotations


class ErrorCode:
    """统一错误码常量表。

    通用错误码用于 HTTP 语义级别的错误，业务错误码用于领域资源未找到或冲突等场景。
    """

    # 通用错误码
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_server_error"

    # 业务错误码
    USER_NOT_FOUND = "user_not_found"
    TRIP_NOT_FOUND = "trip_not_found"
    TRIP_DAY_NOT_FOUND = "trip_day_not_found"
    TRIP_POINT_NOT_FOUND = "trip_point_not_found"
    PACKING_ITEM_NOT_FOUND = "packing_item_not_found"
    COMMUNITY_POST_NOT_FOUND = "community_post_not_found"
    JOB_NOT_FOUND = "job_not_found"
    OUTFIT_NOT_FOUND = "outfit_not_found"
    PHOTO_SPOT_NOT_FOUND = "photo_spot_not_found"
    DUPLICATE_EMAIL = "duplicate_email"
    DUPLICATE_USERNAME = "duplicate_username"
