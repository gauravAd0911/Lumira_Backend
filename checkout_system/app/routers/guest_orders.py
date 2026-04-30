"""
Guest Order Routes
------------------
POST /api/v1/guest-orders                 — place order (requires both OTPs verified)
POST /api/v1/guest-orders/request-lookup  — send email OTP for lookup
POST /api/v1/guest-orders/verify-lookup   — verify OTP → return orders
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import GuestCheckoutSession, OtpChannel, OtpPurpose
from app.schemas.schemas import (
    GuestOrderIn, GuestOrderOut, AddressOut,
    LookupRequestIn, LookupRequestOut,
    LookupVerifyIn, LookupVerifyOut,
)
from app.services.otp_service import (
    create_lookup_session, send_otp, verify_otp,
    require_checkout_session, require_lookup_session,
    expire_secs,
)
from app.services.order_service import create_order, get_orders_by_email

router = APIRouter(prefix="/api/v1/guest-orders", tags=["Guest Orders"])
cfg    = get_settings()


def _addr(a) -> AddressOut | None:
    if not a:
        return None
    return AddressOut(
        id=a.id, full_name=a.full_name, line1=a.line1, line2=a.line2,
        city=a.city, state=a.state, postal_code=a.postal_code,
        country=a.country, phone=a.phone, created_at=a.created_at,
    )

def _out(o) -> GuestOrderOut:
    return GuestOrderOut(
        id=o.id, order_number=o.order_number,
        guest_name=o.guest_name, guest_email=o.guest_email, guest_phone=o.guest_phone,
        email_verified=o.email_verified, sms_verified=o.sms_verified,
        items=o.items, subtotal=o.subtotal, shipping_amount=o.shipping_amount,
        tax_amount=o.tax_amount, discount_amount=o.discount_amount,
        total_amount=o.total_amount, currency=o.currency,
        status=o.status, payment_status=o.payment_status,
        shipping_address=_addr(o.shipping_address), created_at=o.created_at,
    )


@router.post("", response_model=GuestOrderOut, status_code=201)
def place_order(payload: GuestOrderIn, request: Request, db: Session = Depends(get_db)):
    """Place a guest order. Requires session_token (issued only after email + WhatsApp verified)."""
    session = require_checkout_session(db, payload.session_token)
    order   = create_order(db, payload, session, ip_address=request.client.host if request.client else None)
    return _out(order)


@router.post("/request-lookup", response_model=LookupRequestOut, status_code=201)
def request_lookup(payload: LookupRequestIn, request: Request, db: Session = Depends(get_db)):
    """Step 1 of order lookup — sends email OTP only (no WhatsApp needed for read-only access)."""
    session = create_lookup_session(
        db, email=str(payload.email),
        ip_address=request.client.host if request.client else None,
    )
    otp = send_otp(db, session=session, channel=OtpChannel.email, purpose=OtpPurpose.order_lookup)

    return LookupRequestOut(
        session_id=session.id, otp_id=otp.id,
        expires_in_secs=expire_secs(),
        dev_code=otp.plain_code if cfg.dev_show_code else None,
        message=f"[DEV] Code: {otp.plain_code}" if cfg.dev_show_code else "Lookup code sent to your email.",
    )


@router.post("/verify-lookup", response_model=LookupVerifyOut)
def verify_lookup(payload: LookupVerifyIn, db: Session = Depends(get_db)):
    """
    Step 2 — verify email OTP, return all matching guest orders.
    Pass order_number to filter to one specific order.
    """
    session = verify_otp(
        db, session_id=payload.session_id, otp_id=payload.otp_id,
        channel=OtpChannel.email, code=payload.code,
    )
    if not session.session_token:
        raise HTTPException(500, "Session token not issued after verification.")

    require_lookup_session(db, session.session_token)
    orders = get_orders_by_email(db, session.email)

    if payload.order_number:
        orders = [o for o in orders if o.order_number == payload.order_number]

    return LookupVerifyOut(
        orders=[_out(o) for o in orders],
        message=f"Found {len(orders)} order(s) for {session.email}.",
    )
