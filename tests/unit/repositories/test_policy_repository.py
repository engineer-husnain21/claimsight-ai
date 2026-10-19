import uuid

import chromadb
import pytest

from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction


def _chunk(rule_code: str, text: str) -> PolicyChunk:
    return PolicyChunk(
        id=f"policy:{rule_code}",
        source="policy",
        rule_code=rule_code,
        title=f"Title {rule_code}",
        text=text,
    )


@pytest.fixture
def repository() -> PolicyRepository:
    return PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )


async def test_search_when_chunks_stored_returns_most_similar_first(
    repository: PolicyRepository,
) -> None:
    await repository.upsert_chunks(
        [
            _chunk("COV-01", "Annual limit is PKR 1,000,000. The limit resets yearly."),
            _chunk("EXC-02", "Routine dental care is not covered. Dental accidents are."),
        ]
    )

    results = await repository.search("dental treatment", top_k=1)

    assert [chunk.rule_code for chunk in results] == ["EXC-02"]
    assert results[0].title == "Title EXC-02"


async def test_upsert_chunks_when_same_id_replaces_existing_chunk(
    repository: PolicyRepository,
) -> None:
    await repository.upsert_chunks([_chunk("COV-01", "old limit text")])
    await repository.upsert_chunks([_chunk("COV-01", "new limit text")])

    results = await repository.search("limit", top_k=1)

    assert await repository.count() == 1
    assert results[0].text == "new limit text"


async def test_upsert_chunks_when_empty_list_stores_nothing(
    repository: PolicyRepository,
) -> None:
    await repository.upsert_chunks([])

    assert await repository.count() == 0


async def test_list_by_source_when_called_returns_only_that_source_sorted(
    repository: PolicyRepository,
) -> None:
    await repository.upsert_chunks(
        [
            _chunk("COV-01", "Annual limit text."),
            PolicyChunk(
                id="fraud_indicators:FRD-02",
                source="fraud_indicators",
                rule_code="FRD-02",
                title="Amount",
                text="Unusual amount.",
            ),
            PolicyChunk(
                id="fraud_indicators:FRD-01",
                source="fraud_indicators",
                rule_code="FRD-01",
                title="Duplicate",
                text="Duplicate claims.",
            ),
        ]
    )

    chunks = await repository.list_by_source("fraud_indicators")

    assert [chunk.rule_code for chunk in chunks] == ["FRD-01", "FRD-02"]
