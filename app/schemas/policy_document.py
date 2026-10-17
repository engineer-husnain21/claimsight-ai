"""Schema for a raw policy document read from disk."""

from pydantic import BaseModel


class PolicyDocument(BaseModel):
    """One policy markdown file: its name and full text."""

    source: str
    text: str
