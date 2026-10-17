"""Input for the extraction agent."""

from pydantic import BaseModel, Field


class ExtractionInput(BaseModel):
    """Raw claim text submitted by the hospital or patient."""

    claim_text: str = Field(min_length=1, max_length=20_000)
