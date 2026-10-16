from typing import Any

import pytest

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.models.user_role import UserRole
from app.services.token_service import TYPE_ACCESS, TokenService


def _build_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {"jwt_secret_key": "x" * 40, "llm_model": "test-model"}
    values.update(overrides)
    return Settings(**values)


def _build_user() -> User:
    return User(
        id="user-1",
        email="a@example.com",
        full_name="Test User",
        hashed_password="not-a-real-hash",
        role=UserRole.REVIEWER,
    )


def test_decode_token_when_token_is_valid_returns_payload() -> None:
    service = TokenService(_build_settings())
    token = service.create_access_token(_build_user())

    payload = service.decode_token(token, TYPE_ACCESS)

    assert payload.sub == "user-1"
    assert payload.role == "reviewer"
    assert payload.type == TYPE_ACCESS


def test_decode_token_when_type_is_wrong_raises_unauthorized() -> None:
    service = TokenService(_build_settings())
    token = service.create_refresh_token(_build_user())

    with pytest.raises(UnauthorizedError):
        service.decode_token(token, TYPE_ACCESS)


def test_decode_token_when_token_is_garbage_raises_unauthorized() -> None:
    service = TokenService(_build_settings())

    with pytest.raises(UnauthorizedError):
        service.decode_token("not-a-jwt", TYPE_ACCESS)


def test_decode_token_when_secret_differs_raises_unauthorized() -> None:
    issuer = TokenService(_build_settings(jwt_secret_key="a" * 40))
    verifier = TokenService(_build_settings(jwt_secret_key="b" * 40))
    token = issuer.create_access_token(_build_user())

    with pytest.raises(UnauthorizedError):
        verifier.decode_token(token, TYPE_ACCESS)


def test_decode_token_when_token_is_expired_raises_unauthorized() -> None:
    service = TokenService(_build_settings(access_token_expire_minutes=-1))
    token = service.create_access_token(_build_user())

    with pytest.raises(UnauthorizedError):
        service.decode_token(token, TYPE_ACCESS)
