"""Record of one agent run, used for the agent reasoning view."""

from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    """Which agent ran and how long it took."""

    agent: str
    duration_ms: int = Field(ge=0)
