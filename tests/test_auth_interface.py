import pytest
from pydantic import ValidationError

from app.core.auth_service import IAuthService
from app.core.dependencies import StubAuthService
from app.schemas.auth import Token, UserCreate, UserLogin


class TestAuthSchemas:
    def test_user_create_valid(self):
        user = UserCreate(email="test@example.com", password="password123")
        assert user.email == "test@example.com"

    def test_user_create_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="invalid", password="password123")

    def test_user_create_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="123")

    def test_token_schema(self):
        token = Token(access_token="eyJ...", token_type="bearer")
        assert token.token_type == "bearer"


class TestAuthInterface:
    def test_interface_methods_exist(self):
        methods = ["register", "login", "get_user_by_email", "get_user_by_id"]
        for method in methods:
            assert hasattr(IAuthService, method)

    def test_stub_is_instance_of_interface(self):
        service = StubAuthService()
        assert isinstance(service, IAuthService)

    @pytest.mark.asyncio
    async def test_stub_raises_not_implemented(self):
        service = StubAuthService()
        with pytest.raises(NotImplementedError):
            await service.login(UserLogin(email="test@example.com", password="password"))
