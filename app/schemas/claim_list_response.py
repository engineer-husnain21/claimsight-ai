from pydantic import BaseModel

from app.schemas.claim_response import ClaimResponse


class ClaimListResponse(BaseModel):
    items: list[ClaimResponse]
    total: int
    limit: int
    offset: int
