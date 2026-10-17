"""Load policy documents into the ChromaDB vector store.

Usage:
    python -m scripts.ingest_policies
"""

import asyncio
import logging

from app.core.dependencies import get_policy_ingestion_service

logger = logging.getLogger("scripts.ingest_policies")


async def main() -> None:
    """Ingest every policy file and report how many chunks were stored."""
    service = get_policy_ingestion_service()
    stored = await service.ingest_all()
    logger.info("Ingested %d policy chunks into the vector store.", stored)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
