from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error body returned by the API."""

    error: str
    message: str
    request_id: str
