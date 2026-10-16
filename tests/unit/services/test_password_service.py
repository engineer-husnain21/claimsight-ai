from app.services.password_service import PasswordService


async def test_hash_password_when_called_returns_argon2_hash() -> None:
    service = PasswordService()

    hashed = await service.hash_password("CorrectHorse123")

    assert hashed != "CorrectHorse123"
    assert hashed.startswith("$argon2")


async def test_verify_password_when_password_matches_returns_true() -> None:
    service = PasswordService()
    hashed = await service.hash_password("CorrectHorse123")

    assert await service.verify_password("CorrectHorse123", hashed) is True


async def test_verify_password_when_password_is_wrong_returns_false() -> None:
    service = PasswordService()
    hashed = await service.hash_password("CorrectHorse123")

    assert await service.verify_password("WrongHorse123", hashed) is False


async def test_verify_password_when_hash_is_invalid_returns_false() -> None:
    service = PasswordService()

    assert await service.verify_password("anything", "not-a-hash") is False
