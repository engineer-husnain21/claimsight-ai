from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.exceptions import AppError
from app.core.logging import get_logger, request_id_ctx
from app.schemas.error_response import ErrorResponse


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Convert exceptions into consistent JSON error responses."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = get_logger("app.errors")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except AppError as exc:
            self._logger.warning("%s: %s", exc.error_code, exc.message)
            return self._build_response(exc.status_code, exc.error_code, exc.message)
        except Exception:
            # Never leak internal details to the client.
            self._logger.exception("Unhandled error")
            return self._build_response(500, "internal_error", "An unexpected error occurred.")

    @staticmethod
    def _build_response(status_code: int, error: str, message: str) -> JSONResponse:
        body = ErrorResponse(error=error, message=message, request_id=request_id_ctx.get())
        return JSONResponse(status_code=status_code, content=body.model_dump())
