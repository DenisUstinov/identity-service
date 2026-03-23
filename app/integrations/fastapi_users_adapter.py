import logging
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_service import IAuthService
from app.core.notification_service import INotificationService
from app.core.security import pwd_context
from app.db.models import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager[User, int]):
    reset_password_token_secret = "reset_secret"
    verification_token_secret = "verify_secret"

    def __init__(
        self,
        database: SQLAlchemyUserDatabase[User, int],
        notification_service: INotificationService,
    ):
        super().__init__(database)
        self.notification_service = notification_service

    async def on_after_register(self, user: User, request: Any | None = None) -> None:
        await super().on_after_register(user, request)
        token = await self.create_verification_token(user)
        await self.notification_service.send_verification_email(user.email, token.token)


class FastAPIUsersAdapter(IAuthService):
    def __init__(
        self,
        session: AsyncSession,
        notification_service: INotificationService,
    ):
        self.session = session
        self.notification_service = notification_service
        self.user_db = SQLAlchemyUserDatabase[User, int](session, User)
        self.user_manager = UserManager(self.user_db, notification_service)

    async def register(self, user_data: UserCreate) -> UserOut:
        logger.info(f"Registration attempt: email={user_data.email}")

        existing_user = await self.user_db.get_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Registration failed - email exists: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = pwd_context.hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"User registered: email={user.email}, id={user.id}")
        return UserOut(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
        )

    async def login(self, credentials: UserLogin) -> Token:
        logger.info(f"Login attempt: email={credentials.email}")

        user = await self.user_db.get_by_email(credentials.email)
        if not user:
            logger.warning(f"Login failed - user not found: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        verified = pwd_context.verify(credentials.password, user.hashed_password)
        if not verified:
            logger.warning(f"Login failed - wrong password: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        from app.config import settings
        from app.core.security import create_access_token

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        logger.info(f"Login successful: email={user.email}")
        return Token(access_token=access_token, token_type="bearer")

    async def get_user_by_email(self, email: str) -> UserOut | None:
        user = await self.user_db.get_by_email(email)
        if not user:
            return None
        return UserOut(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
        )

    async def get_user_by_id(self, user_id: int) -> UserOut | None:
        user = await self.user_manager.get(user_id)
        if not user:
            return None
        return UserOut(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
        )
