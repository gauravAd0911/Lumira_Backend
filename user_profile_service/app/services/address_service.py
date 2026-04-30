from sqlalchemy.orm import Session
from app.repositories import address_repository
from app.utils.exceptions import UserNotFoundException
from app.db.models.user import User

ADDRESS_NOT_FOUND = "Address not found"


def create_address(db: Session, user_id: str, data: dict):
    """Create new address for user."""

    # ✅ Check user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException()

    # ✅ Add user_id into payload
    data["user_id"] = user_id

    return address_repository.create(db, data)


def get_addresses(db: Session, user_id: str):
    """Get all addresses for user."""
    return address_repository.get_by_user(db, user_id)


def update_address(db: Session, user_id: str, address_id: str, data: dict):
    """Update address."""

    address = address_repository.get_by_id(db, address_id)

    if not address or address.user_id != user_id:
        raise ValueError(ADDRESS_NOT_FOUND)

    return address_repository.update(db, address, data)


def delete_address(db: Session, user_id: str, address_id: str):
    """Delete address."""

    address = address_repository.get_by_id(db, address_id)

    if not address or address.user_id != user_id:
        raise ValueError(ADDRESS_NOT_FOUND)

    return address_repository.delete(db, address)


def set_default_address(db: Session, user_id: str, address_id: str):
    """Set default address."""

    return address_repository.set_default(db, user_id, address_id)
