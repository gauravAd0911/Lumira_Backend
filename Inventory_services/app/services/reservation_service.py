from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.reservation_repo import ReservationRepository
from app.repositories.stock_repo import StockRepository
from app.core.config import settings
from app.core.constants import ReservationStatus


class ReservationService:
    """Business logic for reservation lifecycle."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReservationRepository(db)
        self.stock_repo = StockRepository(db)

    def create_reservation(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        idempotency_key: str | None = None,
    ):
        if idempotency_key:
            existing = self.repo.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        stock = self.stock_repo.get_stock_for_update(product_id, warehouse_id)
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

        if stock.available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "OUT_OF_STOCK",
                    "message": "Requested quantity is not available.",
                    "available_quantity": max(stock.available_quantity, 0),
                },
            )

        stock.reserved_quantity += quantity
        expires_at = datetime.utcnow() + timedelta(seconds=settings.RESERVATION_TTL_SECONDS)
        return self.repo.create(product_id, warehouse_id, quantity, expires_at, idempotency_key)

    def release_reservation(self, reservation_id: int):
        reservation = self.repo.get(reservation_id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

        if reservation.status == ReservationStatus.RELEASED.value:
            return
        if reservation.status == ReservationStatus.COMMITTED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Committed reservation cannot be released")

        stock = self.stock_repo.get_stock_for_update(reservation.product_id, reservation.warehouse_id)
        if stock:
            stock.reserved_quantity = max(0, stock.reserved_quantity - reservation.quantity)

        self.repo.update_status(reservation, ReservationStatus.RELEASED.value)

    def commit_reservation(self, reservation_id: int):
        reservation = self.repo.get(reservation_id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

        if reservation.status == ReservationStatus.COMMITTED.value:
            return

        if reservation.status != ReservationStatus.ACTIVE.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid reservation state")

        if reservation.expires_at < datetime.utcnow():
            self.release_reservation(reservation_id)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reservation expired")

        stock = self.stock_repo.get_stock_for_update(reservation.product_id, reservation.warehouse_id)
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

        if stock.total_quantity < reservation.quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reserved stock is no longer available")

        stock.total_quantity -= reservation.quantity
        stock.reserved_quantity = max(0, stock.reserved_quantity - reservation.quantity)

        self.repo.update_status(reservation, ReservationStatus.COMMITTED.value)
