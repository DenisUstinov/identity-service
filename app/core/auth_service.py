from abc import ABC, abstractmethod

from app.schemas.auth import Token, UserCreate, UserLogin, UserOut


class IAuthService(ABC):
    @abstractmethod
    async def register(self, user_data: UserCreate) -> UserOut:
        pass

    @abstractmethod
    async def login(self, credentials: UserLogin) -> Token:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserOut | None:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> UserOut | None:
        pass
