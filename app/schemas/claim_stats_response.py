from pydantic import BaseModel

from app.models.claim_status import ClaimStatus


class ClaimStatsResponse(BaseModel):
    total: int
    by_status: dict[ClaimStatus, int]
