from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    req: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token_response = await service.register(req)

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        max_age=86400,
    )
    return token_response


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in user and return JWT token",
)
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token_response = await service.login(req)

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_response.access_token}",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400,
    )
    return token_response


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out user and clear cookie",
)
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.update_user(current_user.id, req)
