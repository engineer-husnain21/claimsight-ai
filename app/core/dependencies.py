from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import chromadb
from chromadb.api import ClientAPI
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.clients.gemini_llm_client import GeminiLlmClient
from app.clients.groq_llm_client import GroqLlmClient
from app.clients.llm_client import LlmClient
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, ForbiddenError, UnauthorizedError
from app.core.prompt_loader import PromptLoader
from app.db.session import get_db_session
from app.models.user import User
from app.models.user_role import UserRole
from app.orchestrators.claim_review_orchestrator import ClaimReviewOrchestrator
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.claim_review_repository import ClaimReviewRepository
from app.repositories.policy_document_repository import PolicyDocumentRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.claim_review_service import ClaimReviewService
from app.services.claim_service import ClaimService
from app.services.password_service import PasswordService
from app.services.policy_chunking_service import PolicyChunkingService
from app.services.policy_ingestion_service import PolicyIngestionService
from app.services.policy_retrieval_service import PolicyRetrievalService
from app.services.token_service import TokenService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# auto_error=False so missing credentials use our own error format.
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_password_service() -> PasswordService:
    return PasswordService()


@lru_cache
def get_token_service() -> TokenService:
    return TokenService(get_settings())


def get_user_repository(session: DbSessionDep) -> UserRepository:
    return UserRepository(session)


def get_claim_repository(session: DbSessionDep) -> ClaimRepository:
    return ClaimRepository(session)


def get_audit_log_repository(session: DbSessionDep) -> AuditLogRepository:
    return AuditLogRepository(session)


def get_claim_review_repository(session: DbSessionDep) -> ClaimReviewRepository:
    return ClaimReviewRepository(session)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    return AuthService(user_repository, password_service, token_service)


def get_claim_service(
    claim_repository: Annotated[ClaimRepository, Depends(get_claim_repository)],
    audit_log_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> ClaimService:
    return ClaimService(claim_repository, audit_log_repository)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ClaimServiceDep = Annotated[ClaimService, Depends(get_claim_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    if credentials is None:
        raise UnauthorizedError()
    return await auth_service.get_user_from_access_token(credentials.credentials)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Build a dependency that only lets users with one of the given roles through."""

    async def _check_role(current_user: CurrentUserDep) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError()
        return current_user

    return _check_role


ReviewerDep = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER))]


def build_llm_client(settings: Settings) -> LlmClient:
    """Create the LLM client for the provider selected in settings."""
    provider = settings.llm_provider.lower()

    if provider == "groq":
        if settings.groq_api_key is None:
            raise AppError("The LLM provider is not configured.")
        return GroqLlmClient(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.llm_model,
        )

    if provider == "gemini":
        if settings.google_api_key is None:
            raise AppError("The LLM provider is not configured.")
        return GeminiLlmClient(
            api_key=settings.google_api_key.get_secret_value(),
            model=settings.llm_model,
        )

    raise AppError("The LLM provider is not configured.")


@lru_cache
def get_llm_client() -> LlmClient:
    """Return a shared LLM client instance for FastAPI dependency injection."""
    return build_llm_client(get_settings())


LlmClientDep = Annotated[LlmClient, Depends(get_llm_client)]


@lru_cache
def get_chroma_client() -> ClientAPI:
    """Return a shared ChromaDB client that stores data on disk."""
    return chromadb.PersistentClient(path=get_settings().chroma_persist_dir)


@lru_cache
def get_policy_repository() -> PolicyRepository:
    """Return the shared policy vector store repository."""
    return PolicyRepository(
        client=get_chroma_client(),
        collection_name=get_settings().policy_collection_name,
    )


def get_policy_ingestion_service() -> PolicyIngestionService:
    """Build the service that loads policy files into the vector store."""
    return PolicyIngestionService(
        document_repository=PolicyDocumentRepository(Path(get_settings().policies_dir)),
        policy_repository=get_policy_repository(),
        chunking_service=PolicyChunkingService(),
    )


PolicyRepositoryDep = Annotated[PolicyRepository, Depends(get_policy_repository)]


def get_policy_retrieval_service() -> PolicyRetrievalService:
    """Build the service that searches policy rules."""
    return PolicyRetrievalService(
        policy_repository=get_policy_repository(),
        default_top_k=get_settings().rag_top_k,
    )


PolicyRetrievalServiceDep = Annotated[PolicyRetrievalService, Depends(get_policy_retrieval_service)]


@lru_cache
def get_prompt_loader() -> PromptLoader:
    """Return a shared prompt loader so prompt files are read once."""
    return PromptLoader()


@lru_cache
def get_claim_review_orchestrator() -> ClaimReviewOrchestrator:
    """Build the agent flow once; the graph is compiled a single time."""
    llm_client = get_llm_client()
    prompt_loader = get_prompt_loader()
    return ClaimReviewOrchestrator(
        ExtractionAgent(llm_client, prompt_loader),
        ValidationAgent(llm_client, prompt_loader),
        FraudAgent(llm_client, prompt_loader),
        SummaryAgent(llm_client, prompt_loader),
    )


def get_claim_review_service(
    claim_repository: Annotated[ClaimRepository, Depends(get_claim_repository)],
    claim_review_repository: Annotated[ClaimReviewRepository, Depends(get_claim_review_repository)],
    audit_log_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    policy_retrieval_service: PolicyRetrievalServiceDep,
    orchestrator: Annotated[ClaimReviewOrchestrator, Depends(get_claim_review_orchestrator)],
) -> ClaimReviewService:
    return ClaimReviewService(
        claim_repository=claim_repository,
        claim_review_repository=claim_review_repository,
        audit_log_repository=audit_log_repository,
        policy_retrieval_service=policy_retrieval_service,
        orchestrator=orchestrator,
        llm_model=get_settings().llm_model,
    )


ClaimReviewServiceDep = Annotated[ClaimReviewService, Depends(get_claim_review_service)]


def build_auth_service(session: AsyncSession) -> AuthService:
    """Build AuthService for code that manages its own DB session (MCP, scripts)."""
    return AuthService(UserRepository(session), get_password_service(), get_token_service())


def build_claim_service(session: AsyncSession) -> ClaimService:
    """Build ClaimService for code that manages its own DB session (MCP, scripts)."""
    return ClaimService(ClaimRepository(session), AuditLogRepository(session))
