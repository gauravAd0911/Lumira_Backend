from twilio.rest import Client
from app.config import settings

class TwilioService:
    """Handles SMS notifications."""

    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    def send_sms(self, to: str, message: str) -> None:
        """Send SMS via Twilio."""
        self.client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to
        )