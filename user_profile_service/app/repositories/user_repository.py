from sqlalchemy.orm import Session
from app.db.models.user import User


def get_user(db: Session, user_id: str):
    """Fetch user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """Fetch user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, data: dict):
    """Create new user (avoid duplicate email)."""
    
    # ✅ Check if email already exists
    existing_user = get_user_by_email(db, data.get("email"))
    if existing_user:
        return existing_user  # or raise error if needed

    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: dict):
    """Update user fields dynamically (safe update)."""

    # ❌ Prevent updating restricted fields
    restricted_fields = ["id", "created_at", "updated_at"]

    for key, value in data.items():
        if key not in restricted_fields and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User):
    """Soft delete (deactivate) user."""
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user