from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.db.session import get_engine
from app.middlewares.error_handler_middleware import ErrorHandlerMiddleware
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.request_id_middleware import RequestIdMiddleware
from app.routers.health_router import router as health_router


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

    # The last middleware added is the outermost one (runs first).
    app.add_middleware(ErrorHandlerMiddleware)
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
    return app


app = create_app()
