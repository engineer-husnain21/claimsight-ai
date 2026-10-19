from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.claim_review_output import ClaimReviewOutput
from app.schemas.summary_output import Recommendation


class ClaimReviewResponse(BaseModel):
    """One saved AI review, with every agent's output for the reasoning view."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    requested_by: str
    recommendation: Recommendation
    risk_score: float
    eligible_amount: float | None
    llm_model: str
    result: ClaimReviewOutput
    created_at: datetime
