import uuid

import chromadb
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.mcp_servers.claims_mcp_server import ClaimsMcpServer
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_chunk import PolicyChunk
from app.services.claim_review_service import ClaimReviewService
from app.services.policy_retrieval_service import PolicyRetrievalService
from tests.fakes.fake_embedding_function import FakeEmbeddingFunction


def _unused_claim_review_service_builder(session: AsyncSession) -> ClaimReviewService:
    raise AssertionError("These tests never build the claim review service.")


@pytest.fixture
async def mcp_server() -> ClaimsMcpServer:
    repository = PolicyRepository(
        client=chromadb.EphemeralClient(),
        collection_name=f"test_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFunction(),
    )
    await repository.upsert_chunks(
        [
            PolicyChunk(
                id="policy:EXC-02",
                source="policy",
                rule_code="EXC-02",
                title="Dental",
                text="Dental care is not covered.",
            ),
            PolicyChunk(
                id="policy:COV-01",
                source="policy",
                rule_code="COV-01",
                title="Limit",
                text="Annual limit is PKR 1,000,000.",
            ),
        ]
    )
    # The engine never connects in these tests, so an in-memory URL is enough.
    session_factory = async_sessionmaker(create_async_engine("sqlite+aiosqlite:///:memory:"))
    return ClaimsMcpServer(
        session_factory=session_factory,
        policy_retrieval_service=PolicyRetrievalService(repository, default_top_k=2),
        mcp_user_email=None,
        claim_review_service_builder=_unused_claim_review_service_builder,
    )


async def test_list_tools_when_server_created_exposes_four_tools(
    mcp_server: ClaimsMcpServer,
) -> None:
    tools = await mcp_server.server.list_tools()

    assert {tool.name for tool in tools} == {
        "search_policies",
        "get_claim",
        "list_claims",
        "get_claim_review",
    }


async def test_search_policies_when_query_valid_returns_matching_rules(
    mcp_server: ClaimsMcpServer,
) -> None:
    result = await mcp_server.server.call_tool("search_policies", {"query": "dental", "top_k": 1})

    assert result.structured_content is not None
    rules = result.structured_content["result"]
    assert [rule["rule_code"] for rule in rules] == ["EXC-02"]


async def test_search_policies_when_top_k_too_large_raises_tool_error(
    mcp_server: ClaimsMcpServer,
) -> None:
    with pytest.raises(ToolError):
        await mcp_server.server.call_tool("search_policies", {"query": "dental", "top_k": 50})


async def test_get_claim_when_mcp_user_not_configured_raises_tool_error(
    mcp_server: ClaimsMcpServer,
) -> None:
    with pytest.raises(ToolError, match="MCP user is not configured"):
        await mcp_server.server.call_tool("get_claim", {"claim_id": "abc"})
