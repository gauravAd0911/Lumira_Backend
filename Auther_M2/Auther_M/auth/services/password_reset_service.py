from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from auth.models.user import PasswordResetToken, User
from auth.services.crypto_service import hash_token

RESET_TOKEN_EXPIRY_MINUTES = 10


def _utcnow() -> datetime:
    return datetime.utcnow()


def create_reset_token(db: Session, user: User) -> tuple[str, int]:
    """Create a password reset token and return (plain_token, expiry_seconds)."""

    token = str(uuid.uuid4())
    token_hash = hash_token(token)
    expires_at = _utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)

    record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(record)
    db.commit()

    return token, RESET_TOKEN_EXPIRY_MINUTES * 60


def consume_reset_token(db: Session, token: str) -> User | None:
    """Validate and mark a reset token as used; returns the user if valid."""

    now = _utcnow()
    token_hash = hash_token(token)

    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not record:
        return None

    if record.used_at or record.expires_at < now:
        return None

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        return None

    record.used_at = now
    db.commit()

    return user
