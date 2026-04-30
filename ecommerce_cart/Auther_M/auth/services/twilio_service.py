from __future__ import annotations

import os
from typing import TypedDict

from twilio.rest import Client


class TwilioSendResult(TypedDict, total=False):
    status: str
    sid: str
    error: str


def send_otp_sms(mobile: str, otp_code: str, expiry_minutes: int) -> TwilioSendResult:
    """Send OTP SMS via Twilio.

    Returns a small dict so callers can show a helpful error in the UI.
    """

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not account_sid or not auth_token or not from_number:
        return {"status": "failed", "error": "Twilio environment variables are missing"}

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your OTP is {otp_code}. It expires in {expiry_minutes} minutes.",
            from_=from_number,
            to=mobile,
        )
        return {"status": "sent", "sid": message.sid}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
