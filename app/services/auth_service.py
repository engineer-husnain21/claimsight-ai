from app.core.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.login_request import LoginRequest
from app.schemas.register_request import RegisterRequest
from app.schemas.token_response import TokenResponse
from app.services.password_service import PasswordService
from app.services.token_service import TYPE_ACCESS, TYPE_REFRESH, TokenService

_INVALID_CREDENTIALS = "Invalid email or password."
_INVALID_SESSION = "Invalid or expired token."


class AuthService:
    """Registration, login and token handling."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._token_service = token_service

    async def register(self, request: RegisterRequest) -> User:
        # Public registration never grants elevated roles.
        return await self.create_user(request, UserRole.SUBMITTER)

    async def create_user(self, request: RegisterRequest, role: UserRole) -> User:
        email = request.email.strip().lower()
        if await self._user_repository.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists.")

        user = User(
            email=email,
            full_name=request.full_name.strip(),
            hashed_password=await self._password_service.hash_password(request.password),
            role=role,
        )
        return await self._user_repository.add(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self._user_repository.get_by_email(request.email.strip().lower())
        if user is None:
            # Spend the same effort as a real check so timing does not reveal valid emails.
            await self._password_service.verify_dummy(request.password)
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        password_ok = await self._password_service.verify_password(
            request.password, user.hashed_password
        )
        if not password_ok or not user.is_active:
            raise UnauthorizedError(_INVALID_CREDENTIALS)
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self._token_service.decode_token(refresh_token, TYPE_REFRESH)
        user = await self._user_repository.get_by_id(payload.sub)
        if user is None or not user.is_active:
            raise UnauthorizedError(_INVALID_SESSION)
        return self._issue_tokens(user)

    async def get_user_from_access_token(self, access_token: str) -> User:
        payload = self._token_service.decode_token(access_token, TYPE_ACCESS)
        user = await self._user_repository.get_by_id(payload.sub)
        if user is None or not user.is_active:
            raise UnauthorizedError(_INVALID_SESSION)
        return user

    async def get_active_user_by_email(self, email: str) -> User:
        """Return an active user by email, for trusted local entry points like MCP."""
        user = await self._user_repository.get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            raise UnauthorizedError("MCP user not found or inactive.")
        return user

    def _issue_tokens(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=self._token_service.create_access_token(user),
            refresh_token=self._token_service.create_refresh_token(user),
            expires_in=self._token_service.access_ttl_seconds,
        )
