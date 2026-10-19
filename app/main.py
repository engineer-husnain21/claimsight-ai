from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import request_id_ctx, setup_logging
from app.db.init_db import init_db
from app.db.session import get_engine
from app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.rate_limit_middleware import RateLimitMiddleware
from app.middlewares.request_id_middleware import RequestIdMiddleware
from app.middlewares.security_headers_middleware import SecurityHeadersMiddleware
from app.routers.auth_router import router as auth_router
from app.routers.claim_review_router import router as claim_review_router
from app.routers.claims_router import router as claims_router
from app.routers.health_router import router as health_router
from app.schemas.error_response import ErrorResponse


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup and release the engine on shutdown."""
    await init_db()
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    is_dev = settings.environment == "development"
    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if is_dev else None,
        redoc_url=None,
        openapi_url="/openapi.json" if is_dev else None,
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Report field names only. Never echo submitted values (could be passwords).
        names = {".".join(str(part) for part in error["loc"][1:]) for error in exc.errors()}
        fields = sorted(names - {""})
        message = f"Invalid fields: {', '.join(fields)}" if fields else "Invalid request."
        body = ErrorResponse(
            error="validation_error", message=message, request_id=request_id_ctx.get()
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    # The last middleware added is the outermost one (runs first).
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=settings.rate_limit_per_minute,
        auth_limit=settings.auth_rate_limit_per_minute,
    )
    app.add_middleware(SecurityHeadersMiddleware, strict=not is_dev)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(claims_router, prefix=settings.api_prefix)
    app.include_router(claim_review_router, prefix=settings.api_prefix)
    return app


app = create_app()
