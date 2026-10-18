import uuid

import chromadb
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.dependencies import build_auth_service, build_claim_service
from app.mcp_servers.claims_mcp_server import ClaimsMcpServer
from app.models.user_role import UserRole
from app.repositories.policy_repository import PolicyRepository
from app.schemas.create_claim_request import CreateClaimRequest
from app.schemas.register_request import RegisterRequest
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction

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


def _server(session_factory: async_sessionmaker[AsyncSession], email: str) -> ClaimsMcpServer:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    return ClaimsMcpServer(
        session_factory=session_factory,
        policy_retrieval_service=PolicyRetrievalService(repository, default_top_k=2),
        mcp_user_email=email,
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
