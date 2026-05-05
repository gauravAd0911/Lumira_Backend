from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
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


def _validation_error(error: ValidationError):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.errors())


def _reservation_payload(reservation):
    return {
        "id": reservation.id,
        "reservation_id": str(reservation.id),
        "product_id": reservation.product_id,
        "warehouse_id": reservation.warehouse_id,
        "quantity": reservation.quantity,
        "status": reservation.status,
        "expires_at": reservation.expires_at,
    }


def _parse_reservation_ids(value: str) -> list[int]:
    try:
        reservation_ids = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError:
        reservation_ids = []

    if not reservation_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reservation id must be a number or comma-separated numbers.",
        )

    return reservation_ids


def _batch_response(reservations):
    reservation_ids = ",".join(str(reservation.id) for reservation in reservations)
    return {
        "id": reservation_ids,
        "reservation_id": reservation_ids,
        "status": "ACTIVE",
        "expires_at": min(reservation.expires_at for reservation in reservations),
        "items": [_reservation_payload(reservation) for reservation in reservations],
    }

@router.post("/validate", response_model=StockValidationResponse)
def validate_stock(payload: StockValidationRequest, db: DbSession):
    stock = StockRepository(db).get_stock(payload.product_id, payload.warehouse_id)
    available_quantity = max(stock.available_quantity, 0) if stock else 0
    return StockValidationResponse(
        is_available=available_quantity >= payload.quantity,
        available_quantity=available_quantity,
    )


@router.post("/reservations", status_code=201)
def create_reservation(payload: dict, db: DbSession):
    service = ReservationService(db)

    if isinstance(payload.get("items"), list):
        items = payload.get("items") or []
        if not items:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Reservation items are required.")

        base_idempotency_key = str(payload.get("idempotency_key") or "").strip() or None
        reservations = []
        for index, item in enumerate(items):
            try:
                reservation_payload = ReservationCreateRequest.model_validate(
                    {
                        **item,
                        "idempotency_key": item.get("idempotency_key")
                        or (f"{base_idempotency_key}:{index}" if base_idempotency_key else None),
                    }
                )
            except ValidationError as error:
                _validation_error(error)

            reservations.append(
                service.create_reservation(
                    product_id=reservation_payload.product_id,
                    warehouse_id=reservation_payload.warehouse_id,
                    quantity=reservation_payload.quantity,
                    idempotency_key=reservation_payload.idempotency_key,
                )
            )

        return _batch_response(reservations)

    try:
        reservation_payload = ReservationCreateRequest.model_validate(payload)
    except ValidationError as error:
        _validation_error(error)

    reservation = service.create_reservation(
        product_id=reservation_payload.product_id,
        warehouse_id=reservation_payload.warehouse_id,
        quantity=reservation_payload.quantity,
        idempotency_key=reservation_payload.idempotency_key,
    )
    return ReservationResponse.model_validate(reservation)


@router.delete("/reservations/{reservation_id}", response_model=ReservationActionResponse)
def release_reservation(reservation_id: str, db: DbSession):
    service = ReservationService(db)
    reservation_ids = _parse_reservation_ids(reservation_id)
    for current_id in reservation_ids:
        service.release_reservation(current_id)
    return ReservationActionResponse(message=f"Reservation {reservation_id} released")


@router.post("/reservations/{reservation_id}/commit", response_model=ReservationActionResponse)
def commit_reservation(reservation_id: str, db: DbSession):
    service = ReservationService(db)
    reservation_ids = _parse_reservation_ids(reservation_id)
    for current_id in reservation_ids:
        service.commit_reservation(current_id)
    return ReservationActionResponse(message=f"Reservation {reservation_id} committed")
