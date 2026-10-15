from fastapi import APIRouter

from app.core.dependencies import SettingsDep
from app.schemas.health_response import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health(settings: SettingsDep) -> HealthResponse:
    """Return basic application status."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
    )
