from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.stock_repo import StockRepository
from app.schemas.inventory import StockValidationRequest, StockValidationResponse
from app.schemas.reservation import (
    ReservationActionResponse,
    ReservationCreateRequest,
    ReservationResponse,
)
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])

DbSession = Annotated[Session, Depends(get_db)]

@router.post("/validate", response_model=StockValidationResponse)
def validate_stock(payload: StockValidationRequest, db: DbSession):
    stock = StockRepository(db).get_stock(payload.product_id, payload.warehouse_id)
    available_quantity = max(stock.available_quantity, 0) if stock else 0
    return StockValidationResponse(
        is_available=available_quantity >= payload.quantity,
        available_quantity=available_quantity,
    )


@router.post("/reservations", response_model=ReservationResponse, status_code=201)
def create_reservation(payload: ReservationCreateRequest, db: DbSession):
    return ReservationService(db).create_reservation(
        product_id=payload.product_id,
        warehouse_id=payload.warehouse_id,
        quantity=payload.quantity,
        idempotency_key=payload.idempotency_key,
    )


@router.delete("/reservations/{reservation_id}", response_model=ReservationActionResponse)
def release_reservation(reservation_id: int, db: DbSession):
    ReservationService(db).release_reservation(reservation_id)
    return ReservationActionResponse(message=f"Reservation {reservation_id} released")


@router.post("/reservations/{reservation_id}/commit", response_model=ReservationActionResponse)
def commit_reservation(reservation_id: int, db: DbSession):
    ReservationService(db).commit_reservation(reservation_id)
    return ReservationActionResponse(message=f"Reservation {reservation_id} committed")
