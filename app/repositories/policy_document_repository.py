"""Read policy markdown files from the policies folder."""

import asyncio
from pathlib import Path

from app.core.exceptions import NotFoundError
from app.schemas.policy_document import PolicyDocument


class PolicyDocumentRepository:
    """File access for the source policy documents."""

    def __init__(self, policies_dir: Path) -> None:
        self._policies_dir = policies_dir

    async def list_documents(self) -> list[PolicyDocument]:
        """Return every `.md` policy file, sorted by file name."""
        return await asyncio.to_thread(self._read_documents)

    def _read_documents(self) -> list[PolicyDocument]:
        if not self._policies_dir.is_dir():
            raise NotFoundError("Policies folder not found.")

        return [
            PolicyDocument(source=path.stem, text=path.read_text(encoding="utf-8"))
            for path in sorted(self._policies_dir.glob("*.md"))
        ]
