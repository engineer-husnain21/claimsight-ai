from pathlib import Path

import pytest

from app.core.exceptions import NotFoundError
from app.repositories.policy_document_repository import PolicyDocumentRepository


async def test_list_documents_when_md_files_exist_returns_sorted_documents(
    tmp_path: Path,
) -> None:
    (tmp_path / "b_policy.md").write_text("# B", encoding="utf-8")
    (tmp_path / "a_policy.md").write_text("# A", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")

    documents = await PolicyDocumentRepository(tmp_path).list_documents()

    assert [document.source for document in documents] == ["a_policy", "b_policy"]
    assert documents[0].text == "# A"


async def test_list_documents_when_folder_missing_raises_not_found(
    tmp_path: Path,
) -> None:
    repository = PolicyDocumentRepository(tmp_path / "missing")

    with pytest.raises(NotFoundError):
        await repository.list_documents()
