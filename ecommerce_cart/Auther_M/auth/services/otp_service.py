from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from auth.models.user import User

DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_EXPIRY_MINUTES = 5


def get_otp_expiry_minutes() -> int:
    """Read OTP expiry minutes from env and clamp to a safe range."""

    raw = os.getenv("OTP_EXPIRY_MINUTES", str(DEFAULT_OTP_EXPIRY_MINUTES))
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_OTP_EXPIRY_MINUTES

    return max(1, min(value, 60))


def generate_otp(length: int = DEFAULT_OTP_LENGTH) -> str:
    """Generate a numeric OTP of a given length."""

    length = max(4, min(int(length), 10))
    start = 10 ** (length - 1)
    span = (10 ** length) - start
    return str(secrets.randbelow(span) + start)


@dataclass(frozen=True)
class IssuedOtp:
    """OTP metadata returned when issuing a new OTP."""

    code: str
    expires_at: datetime
    expiry_minutes: int


def issue_otp_for_user(user: User, now: datetime | None = None) -> IssuedOtp:
    """Set OTP fields on a user instance and return the issued OTP."""

    now = now or datetime.utcnow()
    expiry_minutes = get_otp_expiry_minutes()

    code = generate_otp()
    expires_at = now + timedelta(minutes=expiry_minutes)

    user.otp_code = code
    user.otp_expires_at = expires_at
    user.otp_verified_at = None

    return IssuedOtp(code=code, expires_at=expires_at, expiry_minutes=expiry_minutes)


def verify_otp_for_user(user: User, otp: str, now: datetime | None = None) -> bool:
    """Validate a user OTP against stored fields."""

    now = now or datetime.utcnow()

    if not user.otp_code or not user.otp_expires_at:
        return False

    if user.otp_expires_at < now:
        return False

    return user.otp_code == otp


def mark_user_otp_verified(user: User, now: datetime | None = None) -> None:
    """Mark OTP as verified and clear OTP fields."""

    now = now or datetime.utcnow()

    user.is_verified = True
    user.otp_verified_at = now
    user.otp_code = None
    user.otp_expires_at = None
