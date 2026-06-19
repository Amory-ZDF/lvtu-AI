from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str | None = None
    timestamp: datetime
    provider: str | None = None
    warnings: list[str] = Field(default_factory=list)
    page: int | None = None
    page_size: int | None = None
    total: int | None = None
    has_more: bool | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ApiError(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ApiResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T
    meta: ResponseMeta


class ApiErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ApiError
    meta: ResponseMeta
