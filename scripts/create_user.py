"""Create a user with a chosen role.

Usage:
    python -m scripts.create_user --email admin@example.com --full-name "Admin User" --role admin
"""

import argparse
import asyncio
import getpass
import sys

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db
from app.db.session import get_engine, get_session_factory
from app.models.user_role import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.register_request import RegisterRequest
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService

logger = get_logger("scripts.create_user")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a ClaimSight AI user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument(
        "--role",
        choices=[role.value for role in UserRole],
        default=UserRole.REVIEWER.value,
    )
    return parser.parse_args()


def _read_password() -> str:
    # Read from the prompt so the password never lands in shell history.
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    return password


async def _create_user(request: RegisterRequest, role: UserRole) -> None:
    await init_db()
    async with get_session_factory()() as session:
        service = AuthService(
            UserRepository(session),
            PasswordService(),
            TokenService(get_settings()),
        )
        user = await service.create_user(request, role)
        await session.commit()
    logger.info("Created %s user: %s", user.role.value, user.email)
    await get_engine().dispose()


def main() -> None:
    setup_logging()
    args = _parse_args()
    password = _read_password()
    try:
        request = RegisterRequest(email=args.email, full_name=args.full_name, password=password)
        asyncio.run(_create_user(request, UserRole(args.role)))
    except ValidationError:
        logger.error(
            "Invalid input. Use a valid email and a 12+ character password "
            "with a letter and a digit."
        )
        sys.exit(1)
    except AppError as exc:
        logger.error("%s", exc.message)
        sys.exit(1)


if __name__ == "__main__":
    main()
