import pytest

from app.core.dependencies import require_roles
from app.core.exceptions import ForbiddenError
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
