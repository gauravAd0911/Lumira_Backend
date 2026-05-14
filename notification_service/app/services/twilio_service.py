from twilio.rest import Client
from app.config import settings

class TwilioService:
    """Handles SMS notifications."""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER

        if not self.account_sid or not self.auth_token or not self.from_number:
            print("[TwilioService] warning: Twilio configuration is incomplete.")
            print(f"  TWILIO_ACCOUNT_SID set: {bool(self.account_sid)}")
            print(f"  TWILIO_AUTH_TOKEN set: {bool(self.auth_token)}")
            print(f"  TWILIO_PHONE_NUMBER set: {bool(self.from_number)}")

        self.client = Client(self.account_sid, self.auth_token)

    def send_sms(self, to: str, message: str) -> None:
        """Send SMS via Twilio."""
        print(
            f"[TwilioService] sending SMS to {to} from {self.from_number} "
            f"account={self.account_sid[:4]}..."
        )

        try:
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            print(f"[TwilioService] SMS sent successfully to {to}")
        except Exception as e:
            print(f"[TwilioService] SMS send failed for {to}: {e}")
            raise