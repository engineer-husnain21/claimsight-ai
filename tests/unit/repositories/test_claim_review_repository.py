from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models as _models  # noqa: F401  (registers entities on Base.metadata)
from app.db.base import Base
from app.models.claim_review import ClaimReview
from app.repositories.claim_review_repository import ClaimReviewRepository


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db_session:
        yield db_session
    await engine.dispose()


def _review(claim_id: str, risk_score: float, created_at: datetime) -> ClaimReview:
    return ClaimReview(
        claim_id=claim_id,
        requested_by="reviewer-1",
        recommendation="needs_review",
        risk_score=risk_score,
        eligible_amount=1000.0,
        llm_model="test-model",
        result={"summary": {"summary": "test"}},
        created_at=created_at,
    )


async def test_get_latest_for_claim_when_several_reviews_returns_newest(
    session: AsyncSession,
) -> None:
    repository = ClaimReviewRepository(session)
    now = datetime.now(UTC)
    await repository.add(_review("claim-1", 10, now - timedelta(minutes=5)))
    await repository.add(_review("claim-1", 80, now))
    await repository.add(_review("claim-2", 50, now + timedelta(minutes=1)))

    latest = await repository.get_latest_for_claim("claim-1")

    assert latest is not None
    assert latest.risk_score == 80
    assert latest.result == {"summary": {"summary": "test"}}


async def test_get_latest_for_claim_when_never_reviewed_returns_none(
    session: AsyncSession,
) -> None:
    latest = await ClaimReviewRepository(session).get_latest_for_claim("missing")

    assert latest is None
