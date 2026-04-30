# app/services/notification_service.py

from twilio.rest import Client
from app.core.config import settings


class NotificationService:
    """Handles SMS notifications."""

    def __init__(self):
        self.client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)

    def send_delivery_sms(self, phone: str) -> None:
        """Send delivery success message."""
        self.client.messages.create(
            body="Your order has been delivered successfully!",
            from_=settings.TWILIO_PHONE,
            to=phone
        )