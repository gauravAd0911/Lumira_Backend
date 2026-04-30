from __future__ import annotations

import hashlib
import os


def _secret() -> str:
    return os.getenv("OTP_SECRET", os.getenv("JWT_SECRET", "dev-secret"))


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_otp(context_id: str, otp: str) -> str:
    """Hash OTP with a server secret + context id salt."""

    return sha256_hex(f"{_secret()}:{context_id}:{otp}")


def hash_token(token: str) -> str:
    """Hash arbitrary token string."""

    return sha256_hex(f"{_secret()}:{token}")
