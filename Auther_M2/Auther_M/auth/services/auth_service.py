from __future__ import annotations

from sqlalchemy.orm import Session

from auth.models.user import Role, User
from auth.schemas.user_schema import SignupInitiateRequest
from auth.services.identifier_service import normalize_email, normalize_phone
from auth.utils.password import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.query(User).filter(User.phone == phone).first()


def create_pending_user(db: Session, payload: SignupInitiateRequest) -> User:
    """Create or update a pending (unverified) user for signup."""

    email = normalize_email(payload.email)
    phone = normalize_phone(payload.phone)

    existing = get_user_by_email(db, email)
    if existing and existing.is_verified:
        raise ValueError("Email already exists")

    user = existing or User(email=email)

    user.full_name = payload.full_name
    user.phone = phone
    user.password_hash = hash_password(payload.password)
    user.role = Role.CONSUMER
    user.is_active = True
    user.is_verified = False

    if not existing:
        db.add(user)

    db.commit()
    db.refresh(user)

    return user


def mark_user_verified(db: Session, user: User) -> None:
    user.is_verified = True
    db.commit()


def authenticate_by_identifier(db: Session, identifier: str, password: str) -> User | None:
    """Authenticate user by email or phone."""

    ident = identifier.strip()

    user = get_user_by_email(db, normalize_email(ident)) if "@" in ident else get_user_by_phone(db, normalize_phone(ident))
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


