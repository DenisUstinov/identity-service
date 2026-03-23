import logging

from app.core.notification_service import INotificationService

logger = logging.getLogger(__name__)


class ConsoleNotificationAdapter(INotificationService):
    async def send_verification_email(self, email: str, token: str) -> None:
        logger.info(f"[MOCK] Verification email sent to {email} with token {token}")

    async def send_password_reset_email(self, email: str, token: str) -> None:
        logger.info(f"[MOCK] Password reset email sent to {email} with token {token}")
