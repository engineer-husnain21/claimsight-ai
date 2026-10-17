"""Input for the claim review orchestrator."""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.fraud_input import PriorClaim
from app.schemas.policy_chunk import PolicyChunk


class ClaimReviewInput(BaseModel):
    """Everything the agents need, gathered by the service before the run."""

    claim_text: str = Field(min_length=1, max_length=20_000)
    validation_policy_chunks: list[PolicyChunk] = Field(min_length=1)
    fraud_policy_chunks: list[PolicyChunk] = Field(min_length=1)
    prior_claims: list[PriorClaim] = Field(default_factory=list)
    review_date: date
