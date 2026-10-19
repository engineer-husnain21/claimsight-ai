import uuid

import chromadb
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.core.dependencies import build_auth_service, build_claim_service
from app.core.prompt_loader import PromptLoader
from app.mcp_servers.claims_mcp_server import ClaimsMcpServer
from app.models.claim_review import ClaimReview
from app.models.user_role import UserRole
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.claim_review_repository import ClaimReviewRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.claim_review_output import ClaimReviewOutput
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.extraction_output import ExtractionOutput
from app.schemas.fraud_output import FraudOutput
from app.schemas.register_request import RegisterRequest
from app.schemas.summary_output import SummaryOutput
from app.schemas.validation_output import ValidationOutput
from app.services.claim_review_service import ClaimReviewService
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction
from tests.fakes.routing_fake_llm_client import RoutingFakeLlmClient

SUBMITTER_EMAIL = "mcp.submitter@example.com"
REVIEWER_EMAIL = "mcp.reviewer@example.com"
OTHER_EMAIL = "mcp.other@example.com"
PASSWORD = "StrongPassword123"


async def _seed_claim(session_factory: async_sessionmaker[AsyncSession]) -> str:
    async with session_factory() as session:
        auth_service = build_auth_service(session)
        submitter = await auth_service.create_user(
            RegisterRequest(email=SUBMITTER_EMAIL, full_name="Claim Submitter", password=PASSWORD),
            UserRole.SUBMITTER,
        )
        await auth_service.create_user(
            RegisterRequest(email=REVIEWER_EMAIL, full_name="Claim Reviewer", password=PASSWORD),
            UserRole.REVIEWER,
        )
        await auth_service.create_user(
            RegisterRequest(email=OTHER_EMAIL, full_name="Other Submitter", password=PASSWORD),
            UserRole.SUBMITTER,
        )
        claim = await build_claim_service(session).create_claim(
            CreateClaimRequest(
                patient_name="Ahmed Raza",
                policy_number="PK-55821",
                hospital_name="City Care Hospital",
                diagnosis="Acute appendicitis",
                procedure="Laparoscopic appendectomy",
                amount_claimed=253000,
            ),
            submitter,
        )
        await session.commit()
        return claim.id


async def _seed_review(session_factory: async_sessionmaker[AsyncSession], claim_id: str) -> None:
    """Store a finished AI review directly, so no agent has to run."""
    result = ClaimReviewOutput(
        extraction=ExtractionOutput(patient_name="Ahmed Raza"),
        validation=ValidationOutput(is_compliant=True, reasoning="Covered."),
        fraud=FraudOutput(risk_score=12, reasoning="Clean."),
        summary=SummaryOutput(summary="Clean claim.", recommendation="approved"),
        steps=[],
    )
    async with session_factory() as session:
        reviewer = await build_auth_service(session).get_active_user_by_email(REVIEWER_EMAIL)
        session.add(
            ClaimReview(
                claim_id=claim_id,
                requested_by=reviewer.id,
                recommendation="approved",
                risk_score=12,
                eligible_amount=253000,
                llm_model="test-model",
                result=result.model_dump(mode="json"),
            )
        )
        await session.commit()


def _server(session_factory: async_sessionmaker[AsyncSession], email: str) -> ClaimsMcpServer:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    retrieval_service = PolicyRetrievalService(repository, default_top_k=2)
    # The MCP tool only reads reviews, so these agents are never called.
    llm_client = RoutingFakeLlmClient({})
    prompt_loader = PromptLoader()
    orchestrator = ClaimReviewOrchestrator(
        ExtractionAgent(llm_client, prompt_loader),
        ValidationAgent(llm_client, prompt_loader),
        FraudAgent(llm_client, prompt_loader),
        SummaryAgent(llm_client, prompt_loader),
    )

    def build_claim_review_service(session: AsyncSession) -> ClaimReviewService:
        return ClaimReviewService(
            claim_repository=ClaimRepository(session),
            claim_review_repository=ClaimReviewRepository(session),
            audit_log_repository=AuditLogRepository(session),
            policy_retrieval_service=retrieval_service,
            orchestrator=orchestrator,
            llm_model="test-model",
        )

    return ClaimsMcpServer(
        session_factory=session_factory,
        policy_retrieval_service=retrieval_service,
        mcp_user_email=email,
        claim_review_service_builder=build_claim_review_service,
    )


async def test_get_claim_when_user_is_reviewer_returns_claim(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    claim_id = await _seed_claim(session_factory)

    result = await _server(session_factory, REVIEWER_EMAIL).server.call_tool(
        "get_claim", {"claim_id": claim_id}
    )

    assert result.structured_content is not None
    assert result.structured_content["patient_name"] == "Ahmed Raza"


async def test_get_claim_when_user_is_other_submitter_raises_not_found(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    claim_id = await _seed_claim(session_factory)

    with pytest.raises(ToolError, match="Claim not found"):
        await _server(session_factory, OTHER_EMAIL).server.call_tool(
            "get_claim", {"claim_id": claim_id}
        )


async def test_list_claims_when_user_is_reviewer_sees_all_claims(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_claim(session_factory)

    result = await _server(session_factory, REVIEWER_EMAIL).server.call_tool("list_claims", {})

    assert result.structured_content is not None
    assert result.structured_content["total"] == 1


async def test_list_claims_when_user_is_other_submitter_sees_nothing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_claim(session_factory)

    result = await _server(session_factory, OTHER_EMAIL).server.call_tool("list_claims", {})

    assert result.structured_content is not None
    assert result.structured_content["total"] == 0


async def test_get_claim_when_mcp_user_unknown_raises_tool_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(ToolError, match="MCP user not found"):
        await _server(session_factory, "nobody@example.com").server.call_tool(
            "get_claim", {"claim_id": "abc"}
        )


async def test_get_claim_review_when_user_is_reviewer_returns_latest_review(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    claim_id = await _seed_claim(session_factory)
    await _seed_review(session_factory, claim_id)

    result = await _server(session_factory, REVIEWER_EMAIL).server.call_tool(
        "get_claim_review", {"claim_id": claim_id}
    )

    assert result.structured_content is not None
    assert result.structured_content["recommendation"] == "approved"
    assert result.structured_content["result"]["fraud"]["risk_level"] == "low"


async def test_get_claim_review_when_user_is_submitter_raises_tool_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    claim_id = await _seed_claim(session_factory)
    await _seed_review(session_factory, claim_id)

    with pytest.raises(ToolError, match="permission"):
        await _server(session_factory, OTHER_EMAIL).server.call_tool(
            "get_claim_review", {"claim_id": claim_id}
        )


async def test_get_claim_review_when_never_reviewed_raises_tool_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    claim_id = await _seed_claim(session_factory)

    with pytest.raises(ToolError, match="no AI review"):
        await _server(session_factory, REVIEWER_EMAIL).server.call_tool(
            "get_claim_review", {"claim_id": claim_id}
        )
