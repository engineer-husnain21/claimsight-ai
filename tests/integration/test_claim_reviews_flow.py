import json
import uuid
from collections.abc import AsyncIterator

import chromadb
import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.core.dependencies import (
    build_auth_service,
    build_claim_service,
    get_claim_review_orchestrator,
    get_policy_retrieval_service,
    get_token_service,
)
from app.core.prompt_loader import PromptLoader
from app.db.session import get_db_session
from app.main import create_app
from app.models.user_role import UserRole
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.repositories.policy_repository import PolicyRepository
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.policy_chunk import PolicyChunk
from app.schemas.register_request import RegisterRequest
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction
from tests.fakes.routing_fake_llm_client import RoutingFakeLlmClient

API = "/api/v1"
PASSWORD = "StrongPassword123"
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


def _fake_orchestrator() -> ClaimReviewOrchestrator:
    llm_client = RoutingFakeLlmClient(FAKE_REPLIES)
    prompt_loader = PromptLoader()
    return ClaimReviewOrchestrator(
        ExtractionAgent(llm_client, prompt_loader),
        ValidationAgent(llm_client, prompt_loader),
        FraudAgent(llm_client, prompt_loader),
        SummaryAgent(llm_client, prompt_loader),
    )


async def _fake_policy_retrieval_service() -> PolicyRetrievalService:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
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


@pytest.fixture
async def ai_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[httpx.AsyncClient]:
    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    retrieval_service = await _fake_policy_retrieval_service()
    test_app = create_app()
    test_app.dependency_overrides[get_db_session] = override_db_session
    test_app.dependency_overrides[get_claim_review_orchestrator] = _fake_orchestrator
    test_app.dependency_overrides[get_policy_retrieval_service] = lambda: retrieval_service

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def _seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Create a submitter with one claim and a reviewer. Return claim id and auth headers."""
    async with session_factory() as session:
        auth_service = build_auth_service(session)
        submitter = await auth_service.create_user(
            RegisterRequest(
                email="sub@example.com", full_name="Claim Submitter", password=PASSWORD
            ),
            UserRole.SUBMITTER,
        )
        reviewer = await auth_service.create_user(
            RegisterRequest(email="rev@example.com", full_name="Claim Reviewer", password=PASSWORD),
            UserRole.REVIEWER,
        )
        claim = await build_claim_service(session).create_claim(
            CreateClaimRequest(
                patient_name="Ali Khan",
                policy_number="POL-12345",
                hospital_name="City Hospital",
                diagnosis="Acute appendicitis",
                procedure="Appendectomy",
                amount_claimed=150000,
            ),
            submitter,
        )
        await session.commit()

    token_service = get_token_service()
    submitter_headers = {"Authorization": f"Bearer {token_service.create_access_token(submitter)}"}
    reviewer_headers = {"Authorization": f"Bearer {token_service.create_access_token(reviewer)}"}
    return claim.id, submitter_headers, reviewer_headers


async def test_run_ai_review_when_reviewer_calls_it_saves_and_updates_claim(
    ai_client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    claim_id, _, reviewer_headers = await _seed(session_factory)

    response = await ai_client.post(f"{API}/claims/{claim_id}/ai-reviews", headers=reviewer_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["recommendation"] == "needs_review"
    assert body["result"]["fraud"]["risk_level"] == "medium"
    assert body["result"]["steps"][0]["agent"] == "extraction"

    claim = (await ai_client.get(f"{API}/claims/{claim_id}", headers=reviewer_headers)).json()
    assert claim["risk_score"] == 35
    assert claim["ai_summary"] == "Appendectomy claim needs a closer look."


async def test_get_latest_ai_review_when_reviewed_returns_same_review(
    ai_client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    claim_id, _, reviewer_headers = await _seed(session_factory)
    created = await ai_client.post(f"{API}/claims/{claim_id}/ai-reviews", headers=reviewer_headers)

    response = await ai_client.get(
        f"{API}/claims/{claim_id}/ai-reviews/latest", headers=reviewer_headers
    )

    assert response.status_code == 200
    assert response.json()["id"] == created.json()["id"]


async def test_get_latest_ai_review_when_never_reviewed_returns_404(
    ai_client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    claim_id, _, reviewer_headers = await _seed(session_factory)

    response = await ai_client.get(
        f"{API}/claims/{claim_id}/ai-reviews/latest", headers=reviewer_headers
    )

    assert response.status_code == 404


async def test_run_ai_review_when_user_is_submitter_returns_403(
    ai_client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    claim_id, submitter_headers, _ = await _seed(session_factory)

    response = await ai_client.post(
        f"{API}/claims/{claim_id}/ai-reviews", headers=submitter_headers
    )

    assert response.status_code == 403


async def test_run_ai_review_when_not_logged_in_returns_401(
    ai_client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    claim_id, _, _ = await _seed(session_factory)

    response = await ai_client.post(f"{API}/claims/{claim_id}/ai-reviews")

    assert response.status_code == 401
