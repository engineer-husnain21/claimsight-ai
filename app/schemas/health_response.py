from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response body of the health endpoint."""

    status: str
    app_name: str
    environment: str
