import uuid
from pathlib import Path

import chromadb

from app.repositories.policy_document_repository import PolicyDocumentRepository
from app.repositories.policy_repository import PolicyRepository
from app.services.policy_chunking_service import PolicyChunkingService
from app.services.policy_ingestion_service import PolicyIngestionService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction


async def test_ingest_all_when_policies_exist_stores_one_chunk_per_rule(
    tmp_path: Path,
) -> None:
    (tmp_path / "coverage_policy.md").write_text(
        "# Coverage\n\n## COV-01 Limit\nAnnual limit text.\n\n## COV-02 Room\nRoom rent text.\n",
        encoding="utf-8",
    )
    (tmp_path / "exclusions_policy.md").write_text(
        "# Exclusions\n\n## EXC-01 Dental\nDental care is excluded.\n",
        encoding="utf-8",
    )
    policy_repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    service = PolicyIngestionService(
        PolicyDocumentRepository(tmp_path),
        policy_repository,
        PolicyChunkingService(),
    )

    stored = await service.ingest_all()

    assert stored == 3
    assert await policy_repository.count() == 3


async def test_ingest_all_when_run_twice_does_not_duplicate_chunks(
    tmp_path: Path,
) -> None:
    (tmp_path / "policy.md").write_text(
        "# Policy\n\n## COV-01 Limit\nAnnual limit text.\n", encoding="utf-8"
    )
    policy_repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    service = PolicyIngestionService(
        PolicyDocumentRepository(tmp_path),
        policy_repository,
        PolicyChunkingService(),
    )

    await service.ingest_all()
    await service.ingest_all()

    assert await policy_repository.count() == 1
