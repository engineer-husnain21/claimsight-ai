"""Schema for one searchable section of a policy document."""

from pydantic import BaseModel


class PolicyChunk(BaseModel):
    """A single policy rule section prepared for the vector store."""

    id: str
    source: str
    rule_code: str
    title: str
    text: str
