import json
import uuid
from collections.abc import AsyncIterator

import chromadb
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models as _models  # noqa: F401  (registers entities on Base.metadata)
from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.prompt_loader import PromptLoader
from app.db.base import Base
from app.models.audit_log import AuditLog
from app.models.claim import Claim
from app.models.user import User
from app.models.user_role import UserRole
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.claim_review_repository import ClaimReviewRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk
from app.services.claim_review_service import ClaimReviewService
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction
from tests.fakes.routing_fake_llm_client import RoutingFakeLlmClient

FAKE_REPLIES = {
    "extraction assistant": json.dumps(
        {"patient_name": "Ali Khan", "admission_type": "inpatient", "total_amount": 150000}
    ),
    "validation assistant": json.dumps(
        {
            "is_compliant": False,
            "issues": [{"rule_code": "COV-01", "severity": "warning", "message": "Check limit"}],
            "eligible_amount": 140000,
            "reasoning": "Partly covered.",
        }
    ),
    "fraud and anomaly": json.dumps({"risk_score": 35, "flags": [], "reasoning": "Unusual."}),
    "claims review assistant": json.dumps(
        {
            "summary": "Appendectomy claim needs a closer look.",
            "key_points": ["COV-01 limit"],
            "recommendation": "needs_review",
        }
    ),
}


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db_session:
        yield db_session
    await engine.dispose()


def _user(email: str, role: UserRole) -> User:
    return User(email=email, full_name="Test User", hashed_password="not-a-hash", role=role)


async def _policy_retrieval_service(with_rules: bool = True) -> PolicyRetrievalService:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    if with_rules:
        await repository.upsert_chunks(
            [
                PolicyChunk(
                    id="coverage_policy:COV-01",
                    source="coverage_policy",
                    rule_code="COV-01",
                    title="Annual Limit",
                    text="Annual limit is PKR 1,000,000.",
                ),
                PolicyChunk(
                    id="fraud_indicators:FRD-01",
                    source="fraud_indicators",
                    rule_code="FRD-01",
                    title="Duplicate Claims",
                    text="Duplicate claims are fraud.",
                ),
            ]
        )
    return PolicyRetrievalService(repository, default_top_k=2)


async def _service(session: AsyncSession, with_rules: bool = True) -> ClaimReviewService:
    llm_client = RoutingFakeLlmClient(FAKE_REPLIES)
    prompt_loader = PromptLoader()
    return ClaimReviewService(
        claim_repository=ClaimRepository(session),
        claim_review_repository=ClaimReviewRepository(session),
        audit_log_repository=AuditLogRepository(session),
        policy_retrieval_service=await _policy_retrieval_service(with_rules),
        orchestrator=ClaimReviewOrchestrator(
            ExtractionAgent(llm_client, prompt_loader),
            ValidationAgent(llm_client, prompt_loader),
            FraudAgent(llm_client, prompt_loader),
            SummaryAgent(llm_client, prompt_loader),
        ),
        llm_model="test-model",
    )


async def _seed(session: AsyncSession) -> tuple[User, User, Claim]:
    submitter = _user("submitter@example.com", UserRole.SUBMITTER)
    reviewer = _user("reviewer@example.com", UserRole.REVIEWER)
    session.add_all([submitter, reviewer])
    await session.flush()
    claim = Claim(
        claim_number="CLM-TEST-0001",
        patient_name="Ali Khan",
        policy_number="POL-12345",
        hospital_name="City Hospital",
        diagnosis="Acute appendicitis",
        procedure="Appendectomy",
        amount_claimed=150000,
        submitted_by=submitter.id,
    )
    session.add(claim)
    await session.flush()
    return submitter, reviewer, claim


async def test_run_review_when_reviewer_runs_it_saves_review_and_updates_claim(
    session: AsyncSession,
) -> None:
    _, reviewer, claim = await _seed(session)
    service = await _service(session)

    review = await service.run_review(claim.id, reviewer)

    assert review.recommendation == "needs_review"
    assert review.risk_score == 35
    assert review.eligible_amount == 140000
    assert review.llm_model == "test-model"
    assert review.result["validation"]["issues"][0]["rule_code"] == "COV-01"
    assert claim.risk_score == 35
    assert claim.ai_summary == "Appendectomy claim needs a closer look."


async def test_run_review_when_successful_writes_audit_log(session: AsyncSession) -> None:
    _, reviewer, claim = await _seed(session)
    service = await _service(session)

    await service.run_review(claim.id, reviewer)

    logs = (await session.execute(select(AuditLog))).scalars().all()
    assert [log.action for log in logs] == ["claim.ai_reviewed"]
    assert logs[0].user_id == reviewer.id


async def test_run_review_when_user_is_submitter_raises_forbidden(
    session: AsyncSession,
) -> None:
    submitter, _, claim = await _seed(session)
    service = await _service(session)

    with pytest.raises(ForbiddenError):
        await service.run_review(claim.id, submitter)


async def test_run_review_when_reviewer_owns_claim_raises_forbidden(
    session: AsyncSession,
) -> None:
    _, reviewer, claim = await _seed(session)
    claim.submitted_by = reviewer.id
    await session.flush()
    service = await _service(session)

    with pytest.raises(ForbiddenError, match="own claim"):
        await service.run_review(claim.id, reviewer)


async def test_run_review_when_policies_not_loaded_raises_error(
    session: AsyncSession,
) -> None:
    _, reviewer, claim = await _seed(session)
    service = await _service(session, with_rules=False)

    with pytest.raises(AppError, match="ingestion"):
        await service.run_review(claim.id, reviewer)


async def test_get_latest_review_when_never_reviewed_raises_not_found(
    session: AsyncSession,
) -> None:
    _, reviewer, claim = await _seed(session)
    service = await _service(session)

    with pytest.raises(NotFoundError, match="no AI review"):
        await service.get_latest_review(claim.id, reviewer)


async def test_get_latest_review_when_reviewed_returns_review(session: AsyncSession) -> None:
    _, reviewer, claim = await _seed(session)
    service = await _service(session)
    created = await service.run_review(claim.id, reviewer)

    latest = await service.get_latest_review(claim.id, reviewer)

    assert latest.id == created.id
