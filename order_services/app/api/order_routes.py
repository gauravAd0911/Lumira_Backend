import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.core.database import SessionLocal
from app.services.order_service import OrderService
from app.schemas.order_schema import FinalizeOrderRequest, OrderResponse

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


# =========================
# Dependency
# =========================
def get_db():
    """
    Provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _decode_hs256_subject(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        signing_input = f"{parts[0]}.{parts[1]}".encode("utf-8")
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            return None
        secret = jwt_secret.encode("utf-8")
        expected_signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
        actual_signature = _b64url_decode(parts[2])
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        payload = json.loads(_b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError):
        return None
    expires_at = payload.get("exp")
    if isinstance(expires_at, (int, float)) and expires_at < time.time():
        return None
    if payload.get("type") not in {None, "access"}:
        return None
    subject = payload.get("sub")
    return str(subject) if subject else None


def get_current_user_id(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        user_id = _decode_hs256_subject(authorization.split(" ", 1)[1].strip())
        if user_id:
            return user_id

    if x_user_id and x_user_id.strip():
        return x_user_id.strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated user is required.",
    )


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


def _item_dict(item) -> dict:
    return {
        "productId": item.product_id,
        "name": item.product_name,
        "quantity": item.quantity,
        "price": item.price,
    }


def _order_summary(order) -> dict:
    return {
        "id": str(order.id),
        "orderNumber": order.order_number,
        "placedOn": order.created_at.isoformat() if getattr(order, "created_at", None) else None,
        "status": order.status,
        "total": order.total,
        "itemCount": order.item_count,
        "primaryLabel": order.primary_label,
    }


def _order_detail(order, service: OrderService) -> dict:
    detail = _order_summary(order)
    detail.update(
        {
            "items": [_item_dict(item) for item in service.order_repo.get_items_for_order(order.id)],
            "shippingAddress": order.shipping_address,
            "paymentMethod": order.payment_method,
        }
    )
    return detail


# =========================
# Finalize Order
# =========================
@router.post("/finalize", response_model=OrderResponse)
def finalize(
    data: FinalizeOrderRequest,
    db: DBSession,
    user_id: CurrentUserId,
):
    """
    Finalize order after checkout.
    """
    try:
        service = OrderService(db)

        return service.finalize_order(
            data=data.model_dump(),  # ✅ snake_case for service
            user_id=user_id
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("")
def create_order(
    payload: dict,
    db: DBSession,
    user_id: CurrentUserId,
):
    """
    Frontend-compatible order creation endpoint.

    The current frontend posts to /orders. This endpoint accepts the mobile
    order payload directly and the web checkout payload after normalizing its
    nested summary/shipping/payment shape.
    """
    payment_details = payload.get("paymentDetails") or {}
    payment_id = payload.get("paymentId") or payment_details.get("gatewayPaymentId") or payment_details.get("paymentId")
    payment_verified = bool(payment_details.get("verified")) or bool(payment_id)
    if not payment_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment must be verified before order creation.")

    summary = payload.get("summary") or {}
    shipping_details = payload.get("shippingDetails") or {}
    items = payload.get("items") or summary.get("items") or []
    if not items and payload.get("lineItems"):
        items = payload["lineItems"]

    normalized_items = []
    for item in items:
        normalized_items.append(
            {
                "product_id": item.get("productId") or item.get("product_id") or item.get("id"),
                "product_name": item.get("productName") or item.get("name") or item.get("label"),
                "price": item.get("price") or item.get("unitPrice") or item.get("unit_price") or 0,
                "quantity": item.get("quantity") or 0,
                "image_url": item.get("imageUrl") or item.get("image_url"),
            }
        )

    order_data = {
        "total": payload.get("total") or summary.get("totalAmount") or summary.get("total") or payment_details.get("amountPaid"),
        "payment_method": payload.get("paymentMethod") or payment_details.get("provider") or "razorpay",
        "shipping_address": payload.get("shippingAddress") or shipping_details.get("address") or str(shipping_details),
        "item_count": payload.get("itemCount") or sum(int(item.get("quantity") or 0) for item in normalized_items),
        "primary_label": payload.get("primaryLabel") or ", ".join(
            str(item.get("product_name") or "Item") for item in normalized_items[:2]
        ),
        "items": normalized_items,
    }

    try:
        created = OrderService(db).finalize_order(data=order_data, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = OrderService(db).order_repo.get_order_for_user(created["orderNumber"], user_id)
    return _order_detail(order, OrderService(db)) if order else created


# =========================
# Get All Orders
# =========================
@router.get("")
def get_orders(db: DBSession, user_id: CurrentUserId):
    """
    Get all orders for user.
    """
    service = OrderService(db)
    return {"orders": [_order_summary(order) for order in service.order_repo.get_orders_for_user(user_id)]}


# =========================
# Get Order Detail
# =========================
@router.get("/{order_id}")
def get_order(order_id: str, db: DBSession, user_id: CurrentUserId):
    """
    Get single order detail.
    """
    service = OrderService(db)

    order = service.order_repo.get_order_for_user(order_id, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return _order_detail(order, service)


# =========================
# Get Tracking Timeline
# =========================
@router.get("/{order_id}/tracking")
def get_tracking(order_id: str, db: DBSession, user_id: CurrentUserId):
    """
    Get order tracking timeline.
    """
    service = OrderService(db)
    order = service.order_repo.get_order_for_user(order_id, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return service.tracking_repo.get_tracking(order_id)
