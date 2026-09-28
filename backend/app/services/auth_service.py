from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictException, UnauthorizedException, NotFoundException
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse, UserUpdate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, req: RegisterRequest) -> TokenResponse:
        existing = await self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictException(detail="Email is already registered")

        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            hashed_password=get_password_hash(req.password),
        )
        user = await self.user_repo.create(user)

        token = create_access_token(subject=user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def login(self, req: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise UnauthorizedException(detail="Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException(detail="User account is inactive")

        token = create_access_token(subject=user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="User not found")
        return user

    async def update_user(self, user_id: str, req: UserUpdate) -> UserResponse:
        user = await self.get_user_by_id(user_id)
        if req.name is not None:
            user.name = req.name.strip()
        if req.password is not None:
            user.hashed_password = get_password_hash(req.password)

        user = await self.user_repo.update(user)
        return UserResponse.model_validate(user)
