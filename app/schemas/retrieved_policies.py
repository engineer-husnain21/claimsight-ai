"""Policy rules found for one claim, split by which agent needs them."""

from pydantic import BaseModel

from app.schemas.policy_chunk import PolicyChunk


class RetrievedPolicies(BaseModel):
    """Coverage rules for the validation agent and fraud rules for the fraud agent."""

    validation_chunks: list[PolicyChunk]
    fraud_chunks: list[PolicyChunk]
