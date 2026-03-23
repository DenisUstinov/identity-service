from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.auth_service import IAuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.auth import Token, UserOut


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="session")
def test_database_url():
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def engine(test_database_url):
    return create_async_engine(test_database_url, poolclass=NullPool)


@pytest.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine, tables):
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    async def _override():
        yield db_session

    return _override


@pytest.fixture
def override_auth_service():
    mock_service = MagicMock(spec=IAuthService)
    registered_emails = set()

    async def mock_register(user_data):
        if user_data.email in registered_emails:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )
        registered_emails.add(user_data.email)
        return UserOut(id=1, email=user_data.email, is_active=True)

    async def mock_login(credentials):
        if credentials.password == "wrongpassword":
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
            )
        return Token(access_token="test_jwt_token_placeholder", token_type="bearer")

    async def mock_get_user_by_id(user_id: int):
        return UserOut(id=user_id, email="test@example.com", is_active=True)

    async def mock_get_user_by_email(email: str):
        return UserOut(id=1, email=email, is_active=True)

    mock_service.register = AsyncMock(side_effect=mock_register)
    mock_service.login = AsyncMock(side_effect=mock_login)
    mock_service.get_user_by_id = AsyncMock(side_effect=mock_get_user_by_id)
    mock_service.get_user_by_email = AsyncMock(side_effect=mock_get_user_by_email)

    def _override():
        return mock_service

    return _override


@pytest.fixture
def override_get_current_user():
    async def _override():
        return UserOut(id=1, email="test@example.com", is_active=True)

    return _override


@pytest.fixture
async def client(override_get_db, override_auth_service):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = override_auth_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def authorized_client(client, override_get_current_user):
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def auth_token():
    return "test_jwt_token_placeholder"
