from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import CheckoutSession, Product
from app.schemas.schemas import (
    CheckoutIssueOut,
    CheckoutPricingOut,
    CheckoutSessionIn,
    CheckoutSessionOut,
    CheckoutValidateIn,
    CheckoutValidateOut,
)

router = APIRouter(prefix="/api/v1/checkout", tags=["Checkout"])

CHECKOUT_TTL_MINUTES = 15


def _get_user_id(x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None) -> str | None:
    return x_user_id.strip() if x_user_id else None


def _validate_payload(db: Session, payload: CheckoutValidateIn) -> CheckoutValidateOut:
    issues: list[CheckoutIssueOut] = []
    subtotal = Decimal("0")

    product_ids = [item.product_id for item in payload.items]
    products = {
        product.id: product
        for product in db.query(Product).filter(Product.id.in_(product_ids), Product.is_active.is_(True)).all()
    }

    for item in payload.items:
        product = products.get(item.product_id)
        if not product:
            issues.append(
                CheckoutIssueOut(
                    code="PRODUCT_NOT_FOUND",
                    message="Product is not available for checkout.",
                    product_id=item.product_id,
                )
            )
            continue

        if product.stock_qty < item.quantity:
            issues.append(
                CheckoutIssueOut(
                    code="OUT_OF_STOCK",
                    message="Requested quantity is not available.",
                    product_id=item.product_id,
                )
            )
            continue

        subtotal += Decimal(product.price) * item.quantity

    pricing = CheckoutPricingOut(
        subtotal=subtotal,
        shipping=Decimal("0") if subtotal >= Decimal("999") else Decimal("99"),
        total=subtotal + (Decimal("0") if subtotal >= Decimal("999") else Decimal("99")),
    )
    return CheckoutValidateOut(
        cart_valid=not any(issue.code in {"PRODUCT_NOT_FOUND"} for issue in issues),
        delivery_valid=True,
        inventory_valid=not any(issue.code == "OUT_OF_STOCK" for issue in issues),
        pricing=pricing,
        issues=issues,
    )


@router.post("/validate", response_model=CheckoutValidateOut)
def validate_checkout(payload: CheckoutValidateIn, db: Annotated[Session, Depends(get_db)]):
    return _validate_payload(db, payload)


@router.post("/session", response_model=CheckoutSessionOut, status_code=status.HTTP_201_CREATED)
def create_checkout_session(
    payload: CheckoutSessionIn,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str | None, Depends(_get_user_id)] = None,
):
    validation = _validate_payload(db, payload)
    if validation.issues:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CHECKOUT_VALIDATION_FAILED",
                "message": "Checkout validation failed.",
                "issues": [issue.model_dump() for issue in validation.issues],
            },
        )

    expires_at = datetime.utcnow() + timedelta(minutes=CHECKOUT_TTL_MINUTES)
    session = CheckoutSession(
        user_id=user_id,
        guest_token=payload.guest_token,
        address_id=payload.address_id,
        items=[item.model_dump() for item in payload.items],
        pricing=validation.pricing.model_dump(mode="json"),
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return CheckoutSessionOut(
        checkout_session_id=session.id,
        payable_amount=validation.pricing.total,
        currency=validation.pricing.currency,
        expires_at=session.expires_at,
    )
