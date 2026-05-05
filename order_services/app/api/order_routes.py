from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_utils import CurrentUserId, get_active_user_id, get_current_role, resolve_guest_user_id
from app.core.database import SessionLocal
from app.schemas.order_schema import FinalizeOrderRequest
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def _success(message: str, data):
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
    }


def _failure(status_code: int, code: str, message: str):
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": [],
            },
        },
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]




def _resolve_checkout_actor_id(
    payload: dict,
    authorization: str | None,
    x_user_id: str | None,
) -> str:
    active_user_id = get_active_user_id(authorization=authorization, x_user_id=x_user_id)
    if active_user_id != "guest_user":
        return active_user_id

    guest_token = str(payload.get("guestToken") or payload.get("guest_token") or "").strip()
    if guest_token:
        return resolve_guest_user_id(guest_token)

    _failure(
        status.HTTP_401_UNAUTHORIZED,
        "UNAUTHORIZED",
        "Guest token is required for guest checkout orders.",
    )




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
        "assignedToEmployeeId": order.assigned_to_employee_id,
        "assignedByAdminId": order.assigned_by_admin_id,
        "statusNote": order.status_note,
    }


def _order_detail(order, service: OrderService) -> dict:
    detail = _order_summary(order)
    detail.update(
        {
            "items": [_item_dict(item) for item in service.order_repo.get_items_for_order(order.id)],
            "shippingAddress": order.shipping_address,
            "paymentMethod": order.payment_method,
            "assignedToEmployeeId": order.assigned_to_employee_id,
            "assignedByAdminId": order.assigned_by_admin_id,
            "statusNote": order.status_note,
        }
    )
    return detail


def _require_operational_role(role: str):
    if role not in {"admin", "employee"}:
        _failure(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Admin or employee access is required.")


def _allowed_next_statuses(current_status: str):
    transitions = {
        "PLACED": {"CONFIRMED", "PACKED", "CANCELLED", "PAYMENT_FAILED"},
        "CONFIRMED": {"PACKED", "CANCELLED"},
        "PACKED": {"SHIPPED", "CANCELLED"},
        "SHIPPED": {"OUT_FOR_DELIVERY"},
        "OUT_FOR_DELIVERY": {"DELIVERED"},
        "DELIVERED": set(),
        "CANCELLED": set(),
        "PAYMENT_FAILED": set(),
    }
    return transitions.get(str(current_status or "").upper(), set())


@router.post("/finalize")
def finalize(data: FinalizeOrderRequest, db: DBSession, user_id: CurrentUserId):
    try:
        created = OrderService(db).finalize_order(data=data.model_dump(), user_id=user_id)
        return _success("Order finalized successfully.", created)
    except ValueError as exc:
        _failure(400, "ORDER_CREATE_FAILED", str(exc))


@router.post("")
def create_order(
    payload: dict,
    db: DBSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
):
    user_id = _resolve_checkout_actor_id(payload, authorization, x_user_id)
    payment_details = payload.get("paymentDetails") or {}
    payment_id = (
        payload.get("paymentId")
        or payment_details.get("gatewayPaymentId")
        or payment_details.get("paymentId")
    )
    payment_verified = bool(payment_details.get("verified")) or bool(payment_id)
    if not payment_verified:
        _failure(
            status.HTTP_409_CONFLICT,
            "PAYMENT_VERIFICATION_FAILED",
            "Payment must be verified before order creation.",
        )

    summary = payload.get("summary") or {}
    shipping_details = payload.get("shippingDetails") or {}
    items = payload.get("items") or summary.get("items") or []
    if not items and payload.get("lineItems"):
        items = payload["lineItems"]

    normalized_items = [
        {
            "product_id": item.get("productId") or item.get("product_id") or item.get("id"),
            "product_name": item.get("productName") or item.get("name") or item.get("label"),
            "price": item.get("price") or item.get("unitPrice") or item.get("unit_price") or 0,
            "quantity": item.get("quantity") or 0,
            "image_url": item.get("imageUrl") or item.get("image_url"),
        }
        for item in items
    ]

    order_data = {
        "total": payload.get("total")
        or summary.get("totalAmount")
        or summary.get("total")
        or payment_details.get("amountPaid"),
        "subtotal": payload.get("subtotal") or summary.get("subtotal"),
        "shipping_amount": payload.get("shippingAmount") or summary.get("shippingAmount") or summary.get("shipping"),
        "discount_amount": payload.get("discountAmount") or summary.get("discountAmount") or summary.get("discount"),
        "tax_amount": payload.get("taxAmount") or summary.get("taxAmount") or summary.get("tax"),
        "payment_method": payload.get("paymentMethod")
        or payment_details.get("provider")
        or "razorpay",
        "shipping_address": payload.get("shippingAddress")
        or shipping_details.get("address")
        or str(shipping_details),
        "item_count": payload.get("itemCount")
        or sum(int(item.get("quantity") or 0) for item in normalized_items),
        "primary_label": payload.get("primaryLabel")
        or ", ".join(str(item.get("product_name") or "Item") for item in normalized_items[:2]),
        "guest_token": payload.get("guestToken") or payload.get("guest_token"),
        "items": normalized_items,
    }

    try:
        created = OrderService(db).finalize_order(data=order_data, user_id=user_id)
    except ValueError as exc:
        _failure(400, "ORDER_CREATE_FAILED", str(exc))

    service = OrderService(db)
    order = service.order_repo.get_order_for_user(created["orderNumber"], user_id)
    return _success(
        "Order created successfully.",
        _order_detail(order, service) if order else created,
    )


@router.get("")
def get_orders(db: DBSession, user_id: CurrentUserId, role: Annotated[str, Depends(get_current_role)]):
    service = OrderService(db)
    if role in {"admin", "employee"}:
        return _success(
            "Orders fetched successfully.",
            {"orders": [_order_summary(order) for order in service.order_repo.get_all_orders()]},
        )
    return _success(
        "Orders fetched successfully.",
        {"orders": [_order_summary(order) for order in service.order_repo.get_orders_for_user(user_id)]},
    )


@router.get("/{order_id}")
def get_order(order_id: str, db: DBSession, user_id: CurrentUserId, role: Annotated[str, Depends(get_current_role)]):
    service = OrderService(db)
    if role in {"admin", "employee"}:
        order = service.order_repo.get_order(order_id) if str(order_id).isdigit() else service.order_repo.get_order_by_number(order_id)
    else:
        order = service.order_repo.get_order_for_user(order_id, user_id)
    if not order:
        _failure(404, "ORDER_NOT_FOUND", "Order not found")
    return _success("Order fetched successfully.", _order_detail(order, service))


@router.get("/{order_id}/tracking")
def get_tracking(order_id: str, db: DBSession, user_id: CurrentUserId):
    service = OrderService(db)
    order = service.order_repo.get_order_for_user(order_id, user_id)
    if not order:
        _failure(404, "ORDER_NOT_FOUND", "Order not found")
    return _success(
        "Order tracking fetched successfully.",
        {"tracking": service.tracking_repo.get_tracking(order_id)},
    )


@router.patch("/admin/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: dict,
    db: DBSession,
    role: Annotated[str, Depends(get_current_role)],
):
    _require_operational_role(role)
    service = OrderService(db)
    order = service.order_repo.get_order(order_id) if str(order_id).isdigit() else service.order_repo.get_order_by_number(str(order_id))
    if not order:
        _failure(404, "ORDER_NOT_FOUND", "Order not found")

    next_status = str(payload.get("status") or "").upper()
    if not next_status:
        _failure(400, "VALIDATION_ERROR", "Order status is required.")
    if next_status not in _allowed_next_statuses(order.status):
        _failure(409, "INVALID_ORDER_TRANSITION", f"Cannot change order status from {order.status} to {next_status}.")

    order.status_note = payload.get("note")
    order.last_updated_by = payload.get("actorUserId")
    service.order_repo.update_status(order.id, next_status)
    service.tracking_repo.add_tracking(order.id, next_status, payload.get("note") or f"Status updated to {next_status}")
    db.commit()
    refreshed = service.order_repo.get_order(order.id)
    return _success("Order status updated successfully.", _order_detail(refreshed, service))


@router.patch("/admin/{order_id}/assign")
def assign_order(
    order_id: str,
    payload: dict,
    db: DBSession,
    role: Annotated[str, Depends(get_current_role)],
    actor_user_id: CurrentUserId,
):
    _require_operational_role(role)
    employee_id = str(payload.get("employeeId") or payload.get("employee_id") or "").strip()
    if not employee_id:
        _failure(400, "VALIDATION_ERROR", "Employee id is required.")

    service = OrderService(db)
    order = service.order_repo.get_order(order_id) if str(order_id).isdigit() else service.order_repo.get_order_by_number(str(order_id))
    if not order:
        _failure(404, "ORDER_NOT_FOUND", "Order not found")

    order = service.order_repo.assign_order(order.id, employee_id, actor_user_id)
    return _success("Order assigned successfully.", _order_detail(order, service))


@router.get("/admin/dashboard/summary")
def admin_dashboard_summary(
    db: DBSession,
    role: Annotated[str, Depends(get_current_role)],
):
    _require_operational_role(role)
    service = OrderService(db)
    orders = service.order_repo.get_all_orders()
    total_orders = len(orders)
    gross_revenue = round(sum(float(order.total or 0) for order in orders), 2)
    status_breakdown = {}
    for order in orders:
        status_breakdown[order.status] = status_breakdown.get(order.status, 0) + 1

    return _success(
        "Dashboard summary fetched successfully.",
        {
            "total_orders": total_orders,
            "gross_revenue": gross_revenue,
            "average_order_value": round(gross_revenue / total_orders, 2) if total_orders else 0,
            "status_breakdown": status_breakdown,
        },
    )
