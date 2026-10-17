"""Store and search policy chunks in a ChromaDB collection."""

import asyncio

from chromadb.api import ClientAPI
from chromadb.api.types import Embeddable, EmbeddingFunction

from app.schemas.policy_chunk import PolicyChunk


class PolicyRepository:
    """Vector store access for policy rule chunks."""

    def __init__(
        self,
        client: ClientAPI,
        collection_name: str,
        embedding_function: EmbeddingFunction[Embeddable] | None = None,
    ) -> None:
        self._collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert_chunks(self, chunks: list[PolicyChunk]) -> None:
        """Insert new chunks or replace existing ones with the same id."""
        if not chunks:
            return
        await asyncio.to_thread(
            self._collection.upsert,
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source": chunk.source,
                    "rule_code": chunk.rule_code,
                    "title": chunk.title,
                }
                for chunk in chunks
            ],
        )

    async def search(self, query: str, top_k: int) -> list[PolicyChunk]:
        """Return the policy chunks most similar to the query text."""
        result = await asyncio.to_thread(
            self._collection.query,
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas"],
        )
        ids = result["ids"][0]
        documents = (result["documents"] or [[]])[0]
        metadatas = (result["metadatas"] or [[]])[0]

        return [
            PolicyChunk(
                id=chunk_id,
                source=str(metadata["source"]),
                rule_code=str(metadata["rule_code"]),
                title=str(metadata["title"]),
                text=document,
            )
            for chunk_id, document, metadata in zip(ids, documents, metadatas, strict=True)
        ]

    async def count(self) -> int:
        """Return how many chunks are stored."""
        return await asyncio.to_thread(self._collection.count)
