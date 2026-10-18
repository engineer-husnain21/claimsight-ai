"""Search the policy rules for text that matches a question or claim."""

from app.core.exceptions import InvalidRequestError
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk

MAX_QUERY_LENGTH = 500
MAX_TOP_K = 10


class PolicyRetrievalService:
    """Business rules around policy search: input limits and defaults."""

    def __init__(self, policy_repository: PolicyRepository, default_top_k: int) -> None:
        self._policy_repository = policy_repository
        self._default_top_k = default_top_k

    async def search(self, query: str, top_k: int | None = None) -> list[PolicyChunk]:
        """Return the policy rules most similar to the query."""
        cleaned_query = query.strip()
        if not cleaned_query or len(cleaned_query) > MAX_QUERY_LENGTH:
            raise InvalidRequestError(f"Query must be between 1 and {MAX_QUERY_LENGTH} characters.")

        limit = self._default_top_k if top_k is None else top_k
        if not 1 <= limit <= MAX_TOP_K:
            raise InvalidRequestError(f"top_k must be between 1 and {MAX_TOP_K}.")

        return await self._policy_repository.search(cleaned_query, limit)
