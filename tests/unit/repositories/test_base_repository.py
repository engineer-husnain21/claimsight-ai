from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import User, UserRole
from app.repositories.base_repository import BaseRepository


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


def _build_user(email: str) -> User:
    return User(
        email=email,
        full_name="Test User",
        hashed_password="not-a-real-hash",
        role=UserRole.SUBMITTER,
    )


async def test_add_when_entity_is_valid_persists_it(session: AsyncSession) -> None:
    repository = BaseRepository(session, User)

    saved = await repository.add(_build_user("a@example.com"))
    found = await repository.get_by_id(saved.id)

    assert found is not None
    assert found.email == "a@example.com"


async def test_get_by_id_when_id_is_missing_returns_none(session: AsyncSession) -> None:
    repository = BaseRepository(session, User)

    assert await repository.get_by_id("missing-id") is None


async def test_list_all_when_limit_is_set_returns_limited_rows(session: AsyncSession) -> None:
    repository = BaseRepository(session, User)
    for index in range(3):
        await repository.add(_build_user(f"user{index}@example.com"))

    rows = await repository.list_all(limit=2)

    assert len(rows) == 2


async def test_delete_when_entity_exists_removes_it(session: AsyncSession) -> None:
    repository = BaseRepository(session, User)
    saved = await repository.add(_build_user("gone@example.com"))

    await repository.delete(saved)

    assert await repository.get_by_id(saved.id) is None
