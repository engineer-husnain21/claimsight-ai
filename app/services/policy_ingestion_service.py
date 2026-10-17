"""Load policy documents, split them into rule chunks and store them for search."""

from app.repositories.policy_document_repository import PolicyDocumentRepository
from app.repositories.policy_repository import PolicyRepository
from app.services.policy_chunking_service import PolicyChunkingService


class PolicyIngestionService:
    """Build the policy vector store from the markdown policy files."""

    def __init__(
        self,
        document_repository: PolicyDocumentRepository,
        policy_repository: PolicyRepository,
        chunking_service: PolicyChunkingService,
    ) -> None:
        self._document_repository = document_repository
        self._policy_repository = policy_repository
        self._chunking_service = chunking_service

    async def ingest_all(self) -> int:
        """Ingest every policy document and return the number of chunks stored."""
        documents = await self._document_repository.list_documents()
        chunks = [
            chunk
            for document in documents
            for chunk in self._chunking_service.split_document(document.source, document.text)
        ]
        await self._policy_repository.upsert_chunks(chunks)
        return len(chunks)
