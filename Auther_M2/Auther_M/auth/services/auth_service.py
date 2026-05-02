from __future__ import annotations

from sqlalchemy.orm import Session

from auth.models.user import Role, User
from auth.schemas.user_schema import SignupInitiateRequest, UpdateProfileRequest
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

    existing_phone_user = get_user_by_phone(db, phone)
    if existing_phone_user and existing_phone_user.id != (existing.id if existing else None) and existing_phone_user.is_verified:
        raise ValueError("Phone already exists")

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


def update_current_user(db: Session, user: User, payload: UpdateProfileRequest) -> User:
    email = normalize_email(payload.email)
    phone = normalize_phone(payload.phone)

    existing_email_user = get_user_by_email(db, email)
    if existing_email_user and existing_email_user.id != user.id:
        raise ValueError("Email already exists")

    existing_phone_user = get_user_by_phone(db, phone)
    if existing_phone_user and existing_phone_user.id != user.id:
        raise ValueError("Phone already exists")

    user.full_name = payload.full_name
    user.email = email
    user.phone = phone

    db.commit()
    db.refresh(user)
    return user


