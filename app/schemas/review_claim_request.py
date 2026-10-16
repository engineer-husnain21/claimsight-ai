from pydantic import BaseModel, Field, field_validator

from app.models.claim_status import ClaimStatus

REVIEW_DECISIONS = {ClaimStatus.APPROVED, ClaimStatus.REJECTED, ClaimStatus.NEEDS_REVIEW}


class ReviewClaimRequest(BaseModel):
    status: ClaimStatus
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_decision(cls, value: ClaimStatus) -> ClaimStatus:
        if value not in REVIEW_DECISIONS:
            raise ValueError("Status must be approved, rejected or needs_review.")
        return value
