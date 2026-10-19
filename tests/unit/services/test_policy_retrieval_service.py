import uuid

import chromadb
import pytest

from app.core.exceptions import InvalidRequestError
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction


def _chunk(rule_code: str, text: str) -> PolicyChunk:
    return PolicyChunk(
        id=f"policy:{rule_code}",
        source="policy",
        rule_code=rule_code,
        title=rule_code,
        text=text,
    )


@pytest.fixture
async def service() -> PolicyRetrievalService:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    await repository.upsert_chunks(
        [
            _chunk("COV-01", "Annual limit is PKR 1,000,000."),
            _chunk("EXC-02", "Dental care is not covered."),
            _chunk("PRE-03", "MRI needs pre-authorization."),
        ]
    )
    return PolicyRetrievalService(repository, default_top_k=2)


async def test_search_when_query_valid_returns_best_match_first(
    service: PolicyRetrievalService,
) -> None:
    results = await service.search("dental treatment", top_k=1)

    assert [chunk.rule_code for chunk in results] == ["EXC-02"]


async def test_search_when_top_k_missing_uses_default(
    service: PolicyRetrievalService,
) -> None:
    results = await service.search("limit")

    assert len(results) == 2


@pytest.mark.parametrize("query", ["", "   ", "x" * 501])
async def test_search_when_query_invalid_raises_error(
    service: PolicyRetrievalService, query: str
) -> None:
    with pytest.raises(InvalidRequestError):
        await service.search(query)


@pytest.mark.parametrize("top_k", [0, 11])
async def test_search_when_top_k_out_of_range_raises_error(
    service: PolicyRetrievalService, top_k: int
) -> None:
    with pytest.raises(InvalidRequestError):
        await service.search("limit", top_k=top_k)


async def test_retrieve_for_claim_when_called_splits_validation_and_fraud_rules() -> None:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    await repository.upsert_chunks(
        [
            _chunk("COV-01", "Annual limit is PKR 1,000,000."),
            _chunk("PRE-03", "MRI needs pre-authorization."),
            PolicyChunk(
                id="fraud_indicators:FRD-01",
                source="fraud_indicators",
                rule_code="FRD-01",
                title="Duplicate",
                text="Duplicate claims are fraud.",
            ),
            PolicyChunk(
                id="fraud_indicators:FRD-02",
                source="fraud_indicators",
                rule_code="FRD-02",
                title="Amount",
                text="Unusual amounts are fraud.",
            ),
        ]
    )
    service = PolicyRetrievalService(repository, default_top_k=2)

    result = await service.retrieve_for_claim("Knee injury", "MRI knee")

    assert [chunk.rule_code for chunk in result.fraud_chunks] == ["FRD-01", "FRD-02"]
    assert {chunk.rule_code for chunk in result.validation_chunks} == {"COV-01", "PRE-03"}
