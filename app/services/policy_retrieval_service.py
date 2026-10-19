"""Search the policy rules for text that matches a question or claim."""

from app.core.exceptions import InvalidRequestError
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk
from app.schemas.retrieved_policies import RetrievedPolicies

MAX_QUERY_LENGTH = 500
MAX_TOP_K = 10
FRAUD_POLICY_SOURCE = "fraud_indicators"
CLAIM_QUERY_TOP_K = 3

# Topics every claim is checked against, so core rules are never missed.
STANDARD_CLAIM_TOPICS = (
    "annual coverage limit",
    "inpatient room rent limit per day",
    "outpatient treatment limit",
    "required claim documents",
    "pre-authorization for planned admissions and advanced imaging",
    "emergency admission rules",
    "non-medical charges not covered",
    "pre-existing conditions",
)


class PolicyRetrievalService:
    """Business rules around policy search: input limits, defaults and claim context."""

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

    async def retrieve_for_claim(self, diagnosis: str, procedure: str) -> RetrievedPolicies:
        """Collect the coverage rules and all fraud rules relevant to a claim."""
        queries = [
            *STANDARD_CLAIM_TOPICS,
            diagnosis,
            procedure,
            f"{procedure} for {diagnosis}",
        ]
        found: dict[str, PolicyChunk] = {}
        for query in queries:
            if not query.strip():
                continue
            for chunk in await self._policy_repository.search(query, CLAIM_QUERY_TOP_K):
                if chunk.source != FRAUD_POLICY_SOURCE:
                    found[chunk.id] = chunk

        fraud_chunks = await self._policy_repository.list_by_source(FRAUD_POLICY_SOURCE)
        validation_chunks = sorted(found.values(), key=lambda chunk: chunk.rule_code)
        return RetrievedPolicies(validation_chunks=validation_chunks, fraud_chunks=fraud_chunks)
