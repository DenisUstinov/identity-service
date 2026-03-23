import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_service import IAuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.db.session import get_db
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

router = APIRouter()
auth_router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(select(1))
        return {"status": "healthy", "service": "identity-service", "db": "connected"}
    except Exception as err:
        logger.error(f"Health check failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection failed"
        ) from err


@auth_router.post("/register", response_model=UserOut)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
):
    logger.info(f"Registration request received for: {user_data.email}")
    return await auth_service.register(user_data)


@auth_router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
):
    logger.info(f"Login request received for: {credentials.email}")
    return await auth_service.login(credentials)


@auth_router.get("/me", response_model=UserOut)
async def get_me(
    current_user: Annotated[UserOut, Depends(get_current_user)],
):
    logger.debug(f"Profile accessed by user: {current_user.email} (ID: {current_user.id})")
    return current_user


router.include_router(auth_router)
