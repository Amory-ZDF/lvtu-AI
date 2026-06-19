import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.api.responses import error_response
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.schemas.common import ErrorDetail

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        payload = error_response(
            code=exc.code,
            message=exc.message,
            request=request,
            details=exc.details,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            ErrorDetail(field=".".join(str(item) for item in error["loc"]), message=error["msg"])
            for error in exc.errors()
        ]
        payload = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="请求参数校验失败",
            request=request,
            details=details,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error")
        payload = error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务内部错误",
            request=request,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(mode="json"),
        )
