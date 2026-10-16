import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


class PasswordService:
    """Hash and verify passwords with Argon2id."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher()
        # Verified against when the email is unknown, so login timing stays similar.
        self._dummy_hash = self._hasher.hash("dummy-value-for-timing")

    async def hash_password(self, password: str) -> str:
        return await asyncio.to_thread(self._hasher.hash, password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        try:
            return await asyncio.to_thread(self._hasher.verify, hashed_password, password)
        except (VerificationError, InvalidHashError):
            return False

    async def verify_dummy(self, password: str) -> None:
        """Spend the same effort as a real verification and discard the result."""
        await self.verify_password(password, self._dummy_hash)
