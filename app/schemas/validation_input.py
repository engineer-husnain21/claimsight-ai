"""Input for the validation agent."""

from pydantic import BaseModel, Field

from app.schemas.extraction_output import ExtractionOutput
from app.schemas.policy_chunk import PolicyChunk


class ValidationInput(BaseModel):
    """Extracted claim details plus the policy rules retrieved for them."""

    extraction: ExtractionOutput
    policy_chunks: list[PolicyChunk] = Field(min_length=1)
