"""MCP server that exposes ClaimSight features as tools for AI clients.

Run with:
    python -m app.mcp_servers.claims_mcp_server
"""

from collections.abc import Callable
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.dependencies import (
    build_auth_service,
    build_claim_review_service,
    build_claim_service,
    get_policy_retrieval_service,
)
from app.core.exceptions import AppError, UnauthorizedError
from app.db.session import get_session_factory
from app.models.claim_status import ClaimStatus
from app.models.user import User
from app.schemas.claim_response import ClaimResponse
from app.schemas.claim_review_response import ClaimReviewResponse
from app.schemas.policy_chunk import PolicyChunk
from app.services.claim_review_service import ClaimReviewService
from app.services.policy_retrieval_service import PolicyRetrievalService

SERVER_NAME = "claimsight"
SERVER_INSTRUCTIONS = (
    "Tools for the ClaimSight hospital claims platform. Use search_policies to "
    "find insurance policy rules, get_claim or list_claims to read claims, and "
    "get_claim_review to read the latest AI review of a claim. "
    "All tools are read-only and run with the permissions of the configured user."
)
MAX_LIST_LIMIT = 50


class ClaimsMcpServer:
    """Expose policy search and claim lookups as read-only MCP tools."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        policy_retrieval_service: PolicyRetrievalService,
        mcp_user_email: str | None,
        claim_review_service_builder: Callable[[AsyncSession], ClaimReviewService],
    ) -> None:
        self._session_factory = session_factory
        self._policy_retrieval_service = policy_retrieval_service
        self._mcp_user_email = mcp_user_email
        self._claim_review_service_builder = claim_review_service_builder

        self.server = MCPServer(name=SERVER_NAME, instructions=SERVER_INSTRUCTIONS)
        self.server.add_tool(
            self.search_policies,
            name="search_policies",
            description="Find the insurance policy rules most related to a question.",
        )
        self.server.add_tool(
            self.get_claim,
            name="get_claim",
            description="Get one claim by its id.",
        )
        self.server.add_tool(
            self.list_claims,
            name="list_claims",
            description="List claims, newest first, optionally filtered by status.",
        )
        self.server.add_tool(
            self.get_claim_review,
            name="get_claim_review",
            description="Get the latest AI review of a claim (reviewers and admins only).",
        )

    async def search_policies(
        self,
        query: Annotated[str, Field(min_length=1, max_length=500)],
        top_k: Annotated[int, Field(ge=1, le=10)] = 4,
    ) -> list[PolicyChunk]:
        """Return policy rules that match the query."""
        try:
            return await self._policy_retrieval_service.search(query, top_k)
        except AppError as exc:
            raise ToolError(exc.message) from exc

    async def get_claim(
        self, claim_id: Annotated[str, Field(min_length=1, max_length=64)]
    ) -> ClaimResponse:
        """Return one claim the configured user is allowed to see."""
        try:
            async with self._session_factory() as session:
                user = await self._get_mcp_user(session)
                claim = await build_claim_service(session).get_claim(claim_id, user)
                return ClaimResponse.model_validate(claim)
        except AppError as exc:
            raise ToolError(exc.message) from exc

    async def list_claims(
        self,
        status: ClaimStatus | None = None,
        limit: Annotated[int, Field(ge=1, le=MAX_LIST_LIMIT)] = 20,
        offset: Annotated[int, Field(ge=0)] = 0,
    ) -> dict[str, Any]:
        """Return a page of claims the configured user is allowed to see."""
        try:
            async with self._session_factory() as session:
                user = await self._get_mcp_user(session)
                claims, total = await build_claim_service(session).list_claims(
                    user=user, status=status, limit=limit, offset=offset
                )
                items = [
                    ClaimResponse.model_validate(claim).model_dump(mode="json") for claim in claims
                ]
                return {"total": total, "items": items}
        except AppError as exc:
            raise ToolError(exc.message) from exc

    async def get_claim_review(
        self, claim_id: Annotated[str, Field(min_length=1, max_length=64)]
    ) -> ClaimReviewResponse:
        """Return the newest AI review of a claim. Never starts a new review."""
        try:
            async with self._session_factory() as session:
                user = await self._get_mcp_user(session)
                service = self._claim_review_service_builder(session)
                review = await service.get_latest_review(claim_id, user)
                return ClaimReviewResponse.model_validate(review)
        except AppError as exc:
            raise ToolError(exc.message) from exc

    async def _get_mcp_user(self, session: AsyncSession) -> User:
        """Load the user the MCP server acts as, so normal access rules apply."""
        if not self._mcp_user_email:
            raise UnauthorizedError("MCP user is not configured.")
        auth_service = build_auth_service(session)
        return await auth_service.get_active_user_by_email(self._mcp_user_email)


def create_claims_mcp_server() -> ClaimsMcpServer:
    """Wire the MCP server with the real database and policy store."""
    return ClaimsMcpServer(
        session_factory=get_session_factory(),
        policy_retrieval_service=get_policy_retrieval_service(),
        mcp_user_email=get_settings().mcp_user_email,
        claim_review_service_builder=build_claim_review_service,
    )


if __name__ == "__main__":
    create_claims_mcp_server().server.run()
