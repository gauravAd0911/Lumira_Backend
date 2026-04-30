from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from auth.models.user import AuthSession, User
from auth.services.crypto_service import hash_token
from auth.utils.jwt import create_access_token, create_refresh_token, verify_token


def _utcnow() -> datetime:
    return datetime.utcnow()


def _refresh_payload(user: User, session_id: str) -> dict:
    return {
        "user_id": user.id,
        "role": user.role.value,
        "sid": session_id,
    }


def create_session(db: Session, user: User) -> tuple[str, str]:
    """Create a new session and return (access_token, refresh_token)."""

    session = AuthSession(user_id=user.id, refresh_token_hash="")
    db.add(session)
    db.flush()

    access_token = create_access_token({"user_id": user.id, "role": user.role.value})
    refresh_token = create_refresh_token(_refresh_payload(user, session.id))

    session.refresh_token_hash = hash_token(refresh_token)
    session.last_used_at = _utcnow()

    db.commit()
    db.refresh(session)

    return access_token, refresh_token


def refresh_session(db: Session, refresh_token: str) -> tuple[str, str, User]:
    """Rotate refresh token and return (new_access_token, new_refresh_token)."""

    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    sid = payload.get("sid")
    if not sid:
        raise ValueError("Invalid refresh token")

    session = db.query(AuthSession).filter(AuthSession.id == sid).first()
    if not session or session.revoked_at:
        raise ValueError("Session revoked")

    if session.refresh_token_hash != hash_token(refresh_token):
        # token reuse / stolen token
        session.revoked_at = _utcnow()
        db.commit()
        raise ValueError("Session revoked")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise ValueError("User not found")

    new_access = create_access_token({"user_id": user.id, "role": user.role.value})
    new_refresh = create_refresh_token(_refresh_payload(user, session.id))

    session.refresh_token_hash = hash_token(new_refresh)
    session.last_used_at = _utcnow()

    db.commit()

    return new_access, new_refresh, user


def revoke_session(db: Session, refresh_token: str) -> None:
    """Revoke a session by refresh token."""

    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return

    sid = payload.get("sid")
    if not sid:
        return

    session = db.query(AuthSession).filter(AuthSession.id == sid).first()
    if not session or session.revoked_at:
        return

    session.revoked_at = _utcnow()
    db.commit()

