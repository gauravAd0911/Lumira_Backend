from datetime import datetime
from sqlalchemy.orm import Session
from app.models.reservation import Reservation
from app.core.constants import ReservationStatus


def cleanup_expired_reservations(db: Session):
    """Mark expired reservations."""
    now = datetime.utcnow()
    expired = db.query(Reservation).filter(
        Reservation.expires_at < now,
        Reservation.status == ReservationStatus.ACTIVE.value
    ).all()

    for res in expired:
        res.status = ReservationStatus.EXPIRED.value

    db.commit()