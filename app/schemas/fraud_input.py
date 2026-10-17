"""Input for the fraud agent."""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.extraction_output import ExtractionOutput
from app.schemas.policy_chunk import PolicyChunk


class PriorClaim(BaseModel):
    """Short summary of an earlier claim from the same submitter."""

    claim_id: str
    service_date: date | None = None
    total_amount: float | None = None
    diagnosis: str | None = None


class FraudInput(BaseModel):
    """Claim details, fraud rules and claim history to check for anomalies."""

    extraction: ExtractionOutput
    policy_chunks: list[PolicyChunk] = Field(min_length=1)
    prior_claims: list[PriorClaim] = Field(default_factory=list)
    review_date: date
