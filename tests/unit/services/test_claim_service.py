from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.base import Base
from app.models import ClaimStatus, User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.user_repository import UserRepository
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.review_claim_request import ReviewClaimRequest
from app.services.claim_service import ClaimService


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


async def _add_user(session: AsyncSession, email: str, role: UserRole) -> User:
    user = User(
        email=email,
        full_name="Test User",
        hashed_password="not-a-real-hash",
        role=role,
    )
    return await UserRepository(session).add(user)


def _build_request() -> CreateClaimRequest:
    return CreateClaimRequest(
        patient_name="Ali Khan",
        policy_number="POL-12345",
        hospital_name="City Hospital",
        diagnosis="Acute appendicitis",
        procedure="Appendectomy",
        amount_claimed=150000,
    )


def _build_service(session: AsyncSession) -> ClaimService:
    return ClaimService(ClaimRepository(session), AuditLogRepository(session))


async def test_create_claim_when_called_records_audit_log(session: AsyncSession) -> None:
    owner = await _add_user(session, "owner@example.com", UserRole.SUBMITTER)
    service = _build_service(session)

    claim = await service.create_claim(_build_request(), owner)

    logs = await AuditLogRepository(session).list_all()
    assert len(logs) == 1
    assert logs[0].action == "claim.created"
    assert logs[0].resource_id == claim.id


async def test_get_claim_when_submitter_is_not_owner_raises_not_found(
    session: AsyncSession,
) -> None:
    owner = await _add_user(session, "owner@example.com", UserRole.SUBMITTER)
    other = await _add_user(session, "other@example.com", UserRole.SUBMITTER)
    service = _build_service(session)
    claim = await service.create_claim(_build_request(), owner)

    with pytest.raises(NotFoundError):
        await service.get_claim(claim.id, other)


async def test_review_claim_when_reviewer_owns_the_claim_raises_forbidden(
    session: AsyncSession,
) -> None:
    reviewer = await _add_user(session, "reviewer@example.com", UserRole.REVIEWER)
    service = _build_service(session)
    claim = await service.create_claim(_build_request(), reviewer)

    with pytest.raises(ForbiddenError):
        await service.review_claim(
            claim.id, ReviewClaimRequest(status=ClaimStatus.APPROVED), reviewer
        )


async def test_get_claim_stats_when_user_is_submitter_counts_only_own_claims(
    session: AsyncSession,
) -> None:
    owner = await _add_user(session, "owner@example.com", UserRole.SUBMITTER)
    other = await _add_user(session, "other@example.com", UserRole.SUBMITTER)
    service = _build_service(session)
    await service.create_claim(_build_request(), owner)
    await service.create_claim(_build_request(), other)

    stats = await service.get_claim_stats(owner)

    assert stats[ClaimStatus.SUBMITTED] == 1
    assert sum(stats.values()) == 1


async def test_get_claim_stats_when_user_is_reviewer_returns_every_status(
    session: AsyncSession,
) -> None:
    owner = await _add_user(session, "owner@example.com", UserRole.SUBMITTER)
    reviewer = await _add_user(session, "reviewer@example.com", UserRole.REVIEWER)
    service = _build_service(session)
    first = await service.create_claim(_build_request(), owner)
    await service.create_claim(_build_request(), owner)
    await service.review_claim(first.id, ReviewClaimRequest(status=ClaimStatus.APPROVED), reviewer)

    stats = await service.get_claim_stats(reviewer)

    expected = {status: 0 for status in ClaimStatus}
    expected[ClaimStatus.SUBMITTED] = 1
    expected[ClaimStatus.APPROVED] = 1
    assert stats == expected
