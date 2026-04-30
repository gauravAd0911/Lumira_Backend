from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.reservation import Reservation


class ReservationRepository:
    """
    Handles reservation database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        expires_at: datetime,
        idempotency_key: str | None,
    ) -> Reservation:
        reservation = Reservation(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            status="ACTIVE",
            expires_at=expires_at,
            idempotency_key=idempotency_key,
        )

        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)

        return reservation

    def get(self, reservation_id: int) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.id == reservation_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_idempotency_key(self, key: str) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.idempotency_key == key)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_status(self, reservation: Reservation, status: str) -> None:
        reservation.status = status
        self.db.commit()