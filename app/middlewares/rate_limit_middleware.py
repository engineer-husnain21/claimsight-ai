import math
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.logging import get_logger, request_id_ctx
from app.schemas.error_response import ErrorResponse

WINDOW_SECONDS = 60.0
MAX_TRACKED_BUCKETS = 10_000
STRICT_PATH_SUFFIXES = ("/auth/login", "/auth/register", "/auth/refresh")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests per client IP with an in-memory sliding window.

    Auth endpoints get a stricter limit to slow down password guessing.
    State lives in this process only; use a shared store (e.g. Redis) if the
    app is ever scaled to several workers.
    """

    def __init__(self, app: ASGIApp, general_limit: int, auth_limit: int) -> None:
        super().__init__(app)
        self._general_limit = general_limit
        self._auth_limit = auth_limit
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._logger = get_logger("app.rate_limit")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        is_strict = request.url.path.endswith(STRICT_PATH_SUFFIXES)
        bucket = f"{client_ip}:{'auth' if is_strict else 'general'}"
        limit = self._auth_limit if is_strict else self._general_limit

        retry_after = self._register_hit(bucket, limit)
        if retry_after is not None:
            self._logger.warning("Rate limit exceeded for %s", bucket)
            return self._build_limited_response(retry_after)
        return await call_next(request)

    def _register_hit(self, bucket: str, limit: int) -> int | None:
        """Record a hit. Return seconds to wait if the limit is exceeded, else None."""
        now = time.monotonic()
        if len(self._hits) > MAX_TRACKED_BUCKETS:
            self._purge_stale(now)

        hits = self._hits[bucket]
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()

        if len(hits) >= limit:
            return max(1, math.ceil(WINDOW_SECONDS - (now - hits[0])))
        hits.append(now)
        return None

    def _purge_stale(self, now: float) -> None:
        stale = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= WINDOW_SECONDS
        ]
        for key in stale:
            del self._hits[key]

    @staticmethod
    def _build_limited_response(retry_after: int) -> JSONResponse:
        body = ErrorResponse(
            error="rate_limited",
            message="Too many requests. Please try again later.",
            request_id=request_id_ctx.get(),
        )
        return JSONResponse(
            status_code=429,
            content=body.model_dump(),
            headers={"Retry-After": str(retry_after)},
        )
