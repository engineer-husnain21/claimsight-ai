from fastapi import APIRouter, status

from app.core.dependencies import AuthServiceDep, CurrentUserDep
from app.schemas.login_request import LoginRequest
from app.schemas.refresh_request import RefreshRequest
from app.schemas.register_request import RegisterRequest
from app.schemas.token_response import TokenResponse
from app.schemas.user_response import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, auth_service: AuthServiceDep) -> UserResponse:
    user = await auth_service.register(request)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.refresh(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(current_user)
