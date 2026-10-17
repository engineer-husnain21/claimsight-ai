"""Fraud and anomaly check result produced by the fraud agent."""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

RiskLevel = Literal["low", "medium", "high"]

MEDIUM_RISK_THRESHOLD = 30
HIGH_RISK_THRESHOLD = 70


class FraudFlag(BaseModel):
    """One fraud indicator found on the claim."""

    rule_code: str
    message: str


class FraudOutput(BaseModel):
    """Risk score from 0 (clean) to 100 (very likely fraud) with the reasons."""

    risk_score: int = Field(ge=0, le=100)
    flags: list[FraudFlag] = Field(default_factory=list)
    reasoning: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def risk_level(self) -> RiskLevel:
        """Bucket the score so every part of the app uses the same thresholds."""
        if self.risk_score >= HIGH_RISK_THRESHOLD:
            return "high"
        if self.risk_score >= MEDIUM_RISK_THRESHOLD:
            return "medium"
        return "low"
