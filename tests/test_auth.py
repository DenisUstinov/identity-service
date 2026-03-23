import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"
    assert response.json()["db"] == "connected"


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "password": "securepassword123",
        "username": "testuser",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    assert "email" in response.json()
    assert response.json()["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_register_user_already_exists(client: AsyncClient):
    user_data = {
        "email": "existing@example.com",
        "password": "securepassword123",
        "username": "existinguser",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    credentials = {"email": "test@example.com", "password": "securepassword123"}
    response = await client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    credentials = {"email": "test@example.com", "password": "wrongpassword"}
    response = await client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_me_success(authorized_client: AsyncClient, auth_token: str):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await authorized_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "email" in response.json()


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_verify_password_success():
    from app.core.security import get_password_hash, verify_password

    plain = "test_password_123"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    from app.core.security import get_password_hash, verify_password

    plain = "correct_password"
    hashed = get_password_hash(plain)
    assert verify_password("wrong_password", hashed) is False


def test_get_password_hash_returns_string():
    from app.core.security import get_password_hash

    result = get_password_hash("any_password")
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_access_token_returns_jwt():

    from app.core.security import create_access_token

    token = create_access_token(data={"sub": "1", "email": "test@example.com"})
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # JWT has 3 parts


def test_decode_token_success():
    from app.core.security import create_access_token, decode_token

    payload = {"sub": "42", "email": "user@example.com"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"


def test_decode_token_invalid():
    from app.core.security import decode_token

    result = decode_token("invalid.token.here")
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_found(db_session, override_auth_service):
    from app.integrations.fastapi_users_adapter import FastAPIUsersAdapter
    from app.integrations.notification_adapter import ConsoleNotificationAdapter

    adapter = FastAPIUsersAdapter(db_session, ConsoleNotificationAdapter())

    # Мокаем вызов БД
    from unittest.mock import AsyncMock, patch

    mock_user = type("MockUser", (), {"id": 1, "email": "found@example.com", "is_active": True})()

    with patch.object(adapter.user_db, "get_by_email", new=AsyncMock(return_value=mock_user)):
        result = await adapter.get_user_by_email("found@example.com")
        assert result is not None
        assert result.email == "found@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session, override_auth_service):
    from unittest.mock import AsyncMock, patch

    from app.integrations.fastapi_users_adapter import FastAPIUsersAdapter
    from app.integrations.notification_adapter import ConsoleNotificationAdapter

    adapter = FastAPIUsersAdapter(db_session, ConsoleNotificationAdapter())

    with patch.object(adapter.user_db, "get_by_email", new=AsyncMock(return_value=None)):
        result = await adapter.get_user_by_email("notfound@example.com")
        assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_found(db_session, override_auth_service):
    from unittest.mock import AsyncMock, patch

    from app.integrations.fastapi_users_adapter import FastAPIUsersAdapter
    from app.integrations.notification_adapter import ConsoleNotificationAdapter

    adapter = FastAPIUsersAdapter(db_session, ConsoleNotificationAdapter())

    mock_user = type("MockUser", (), {"id": 99, "email": "byid@example.com", "is_active": True})()

    with patch.object(adapter.user_manager, "get", new=AsyncMock(return_value=mock_user)):
        result = await adapter.get_user_by_id(99)
        assert result is not None
        assert result.id == 99


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session, override_auth_service):
    from unittest.mock import AsyncMock, patch

    from app.integrations.fastapi_users_adapter import FastAPIUsersAdapter
    from app.integrations.notification_adapter import ConsoleNotificationAdapter

    adapter = FastAPIUsersAdapter(db_session, ConsoleNotificationAdapter())

    with patch.object(adapter.user_manager, "get", new=AsyncMock(return_value=None)):
        result = await adapter.get_user_by_id(999)
        assert result is None
