from sqlalchemy.orm import Session
from app.db.models.address import Address


def create(db: Session, data: dict):
    if data.get("is_default"):
        db.query(Address).filter(Address.user_id == data["user_id"]).update({"is_default": False})

    address = Address(**data)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def get_by_user(db: Session, user_id: str):
    return db.query(Address).filter(Address.user_id == user_id).all()


def get_by_id(db: Session, address_id: str):
    return db.query(Address).filter(Address.id == address_id).first()


def update(db: Session, address: Address, data: dict):
    for key, value in data.items():
        if value is not None:
            setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address


def delete(db: Session, address: Address):
    user_id = address.user_id
    address_id = address.id
    was_default = address.is_default
    db.delete(address)
    if was_default:
        replacement = db.query(Address).filter(Address.user_id == user_id, Address.id != address_id).first()
        if replacement:
            replacement.is_default = True
    db.commit()
    return {"message": "Deleted successfully"}


def set_default(db: Session, user_id: str, address_id: str):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id,
    ).first()
    if not address:
        raise ValueError("Address not found")

    # Reset all
    db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})

    # Set selected
    address.is_default = True

    db.commit()
    db.refresh(address)
    return address
