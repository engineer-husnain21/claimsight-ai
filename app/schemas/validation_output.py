"""Policy check result produced by the validation agent."""

from typing import Literal

from pydantic import BaseModel, Field

IssueSeverity = Literal["info", "warning", "critical"]


class PolicyIssue(BaseModel):
    """One policy rule the claim breaks or needs attention on."""

    rule_code: str
    severity: IssueSeverity
    message: str


class ValidationOutput(BaseModel):
    """Whether the claim follows policy, with issues and the payable amount."""

    is_compliant: bool
    issues: list[PolicyIssue] = Field(default_factory=list)
    eligible_amount: float | None = Field(default=None, ge=0)
    reasoning: str
