import pytest
from pydantic import SecretStr

from app.clients.gemini_llm_client import GeminiLlmClient
from app.clients.groq_llm_client import GroqLlmClient
from app.core.config import get_settings
from app.core.dependencies import build_llm_client, require_roles
from app.core.exceptions import AppError, ForbiddenError
from app.models.user import User
from app.models.user_role import UserRole


def _build_user(role: UserRole) -> User:
    return User(
        id="user-1",
        email="a@example.com",
        full_name="Test User",
        hashed_password="not-a-real-hash",
        role=role,
    )


async def test_require_roles_when_role_is_allowed_returns_user() -> None:
    checker = require_roles(UserRole.ADMIN, UserRole.REVIEWER)
    user = _build_user(UserRole.REVIEWER)

    assert await checker(user) is user


async def test_require_roles_when_role_is_not_allowed_raises_forbidden() -> None:
    checker = require_roles(UserRole.ADMIN)

    with pytest.raises(ForbiddenError):
        await checker(_build_user(UserRole.SUBMITTER))


def test_build_llm_client_when_provider_groq_returns_groq_client() -> None:
    settings = get_settings().model_copy(
        update={"llm_provider": "groq", "groq_api_key": SecretStr("test-key")}
    )

    assert isinstance(build_llm_client(settings), GroqLlmClient)


def test_build_llm_client_when_provider_gemini_returns_gemini_client() -> None:
    settings = get_settings().model_copy(
        update={"llm_provider": "gemini", "google_api_key": SecretStr("test-key")}
    )

    assert isinstance(build_llm_client(settings), GeminiLlmClient)


def test_build_llm_client_when_key_missing_raises_error() -> None:
    settings = get_settings().model_copy(update={"llm_provider": "groq", "groq_api_key": None})

    with pytest.raises(AppError):
        build_llm_client(settings)


def test_build_llm_client_when_provider_unknown_raises_error() -> None:
    settings = get_settings().model_copy(update={"llm_provider": "unknown"})

    with pytest.raises(AppError):
        build_llm_client(settings)
