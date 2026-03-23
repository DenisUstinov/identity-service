import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_service import IAuthService
from app.core.notification_service import INotificationService
from app.core.security import decode_token, oauth2_scheme
from app.db.session import get_db
from app.integrations.fastapi_users_adapter import FastAPIUsersAdapter
from app.integrations.notification_adapter import ConsoleNotificationAdapter
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

logger = logging.getLogger(__name__)


class StubAuthService(IAuthService):
    async def register(self, user_data: UserCreate) -> UserOut:
        raise NotImplementedError

    async def login(self, credentials: UserLogin) -> Token:
        raise NotImplementedError

    async def get_user_by_email(self, email: str) -> UserOut | None:
        raise NotImplementedError

    async def get_user_by_id(self, user_id: int) -> UserOut | None:
        raise NotImplementedError


async def get_notification_service() -> INotificationService:
    return ConsoleNotificationAdapter()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    notification_service: Annotated[INotificationService, Depends(get_notification_service)],
) -> IAuthService:
    return FastAPIUsersAdapter(session, notification_service)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        logger.warning("Invalid token payload")
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        logger.warning("Missing user ID in token payload")
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user ID format in token: {user_id}")
        raise credentials_exception from None

    user = await auth_service.get_user_by_id(user_id_int)
    if user is None:
        logger.warning(f"User not found for ID: {user_id_int}")
        raise credentials_exception

    return user


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
NotificationServiceDep = Annotated[INotificationService, Depends(get_notification_service)]
AuthServiceDep = Annotated[IAuthService, Depends(get_auth_service)]
