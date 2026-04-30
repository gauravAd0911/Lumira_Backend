from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.utils.exceptions import UserNotFoundException
from app.utils.validators import validate_phone, validate_required_string


def get_user(db: Session, user_id: str):
    """Fetch current user profile."""
    user = user_repository.get_user(db, user_id)

    if not user:
        raise UserNotFoundException()

    return user


def update_user(db: Session, user_id: str, data):
    """Update user profile."""

    user = user_repository.get_user(db, user_id)

    if not user:
        raise UserNotFoundException()

    # ✅ Support both dict and Pydantic
    if hasattr(data, "dict"):
        update_data = data.dict(exclude_unset=True)
    else:
        update_data = data

    # ✅ Validation
    if "full_name" in update_data:
        validate_required_string(update_data["full_name"], "Full name")

    if "phone" in update_data:
        validate_phone(update_data["phone"])

    # ❌ Prevent updating restricted fields
    update_data.pop("id", None)
    update_data.pop("created_at", None)
    update_data.pop("updated_at", None)

    # ✅ Update via repository
    return user_repository.update_user(db, user, update_data)