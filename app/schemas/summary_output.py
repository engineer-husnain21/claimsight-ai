"""Reviewer-facing summary produced by the summary agent."""

from typing import Literal

from pydantic import BaseModel, Field

Recommendation = Literal["approved", "rejected", "needs_review"]


class SummaryOutput(BaseModel):
    """Short summary, key points and a suggested decision for the reviewer."""

    summary: str
    key_points: list[str] = Field(default_factory=list, max_length=6)
    recommendation: Recommendation
