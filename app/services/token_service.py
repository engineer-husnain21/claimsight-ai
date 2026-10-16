import uuid
from datetime import timedelta
from typing import Any

import jwt
from pydantic import ValidationError

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.schemas.token_payload import TokenPayload

TYPE_ACCESS = "access"
TYPE_REFRESH = "refresh"
_INVALID_MESSAGE = "Invalid or expired token."


class TokenService:
    """Create and validate signed JWTs."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.access_token_expire_minutes)
        self._refresh_ttl = timedelta(days=settings.refresh_token_expire_days)

    @property
    def access_ttl_seconds(self) -> int:
        return int(self._access_ttl.total_seconds())

    def create_access_token(self, user: User) -> str:
        return self._encode(user, TYPE_ACCESS, self._access_ttl)

    def create_refresh_token(self, user: User) -> str:
        return self._encode(user, TYPE_REFRESH, self._refresh_ttl)

    def decode_token(self, token: str, expected_type: str) -> TokenPayload:
        """Validate signature, expiry and token type. Raise UnauthorizedError on failure."""
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": ["exp", "sub", "type", "jti"]},
            )
            payload = TokenPayload.model_validate(claims)
        except (jwt.PyJWTError, ValidationError) as exc:
            raise UnauthorizedError(_INVALID_MESSAGE) from exc

        if payload.type != expected_type:
            raise UnauthorizedError(_INVALID_MESSAGE)
        return payload

    def _encode(self, user: User, token_type: str, ttl: timedelta) -> str:
        now = utc_now()
        claims: dict[str, Any] = {
            "sub": user.id,
            "role": user.role.value,
            "type": token_type,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + ttl,
        }
        return jwt.encode(claims, self._secret, algorithm=self._algorithm)
