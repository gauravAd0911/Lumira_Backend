from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from auth.models.user import Role, User
from auth.schemas.user_schema import UserCreate
from auth.services.otp_service import issue_otp_for_user, mark_user_otp_verified, verify_otp_for_user
from auth.utils.password import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch user by email."""

    return db.query(User).filter(User.email == email).first()


def get_user_by_mobile(db: Session, mobile: str) -> User | None:
    """Fetch user by mobile."""

    return db.query(User).filter(User.mobile == mobile).first()


def create_or_update_pending_user(db: Session, user_data: UserCreate) -> tuple[User, str, int, bool]:
    """Create or update a pending user and issue a fresh OTP.

    Returns: (user, otp_code, otp_expiry_minutes, created_new)
    """

    existing_by_email = get_user_by_email(db, user_data.email)
    existing_by_mobile = get_user_by_mobile(db, user_data.mobile)

    if existing_by_mobile and existing_by_mobile.email != user_data.email:
        raise ValueError("Mobile number already used")

    if existing_by_email and existing_by_email.is_verified:
        raise ValueError("Email already exists")

    user = existing_by_email or User(email=user_data.email)
    created_new = existing_by_email is None

    user.full_name = user_data.full_name
    user.mobile = user_data.mobile
    user.password_hash = hash_password(user_data.password)
    user.role = Role(user_data.role)
    user.is_active = True
    user.is_verified = False

    issued = issue_otp_for_user(user)

    if created_new:
        db.add(user)

    db.commit()
    db.refresh(user)

    return user, issued.code, issued.expiry_minutes, created_new


def verify_user_otp(db: Session, email: str, otp: str) -> User | None:
    """Verify the user's OTP and mark the account as verified."""

    user = get_user_by_email(db, email)
    if not user:
        return None

    if not verify_otp_for_user(user, otp):
        return None

    mark_user_otp_verified(user, now=datetime.utcnow())
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user by email + password."""

    user = get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user

    return None
