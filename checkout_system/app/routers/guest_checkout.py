"""
Guest Checkout Routes
---------------------
POST /api/v1/guest-checkout/request-verification  — send email + WhatsApp OTPs
POST /api/v1/guest-checkout/verify                — verify one channel
POST /api/v1/guest-checkout/resend-otp            — resend with cooldown
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import GuestCheckoutSession, OtpChannel, OtpPurpose
from app.schemas.schemas import (
    RequestVerificationIn, RequestVerificationOut, OtpChannelInfo,
    VerifyOtpIn, VerifyOtpOut,
    ResendOtpIn, ResendOtpOut,
)
from app.services.otp_service import (
    get_or_create_session, send_otp, verify_otp,
    expire_secs, mask_email, mask_phone,
)

router = APIRouter(prefix="/api/v1/guest-checkout", tags=["Guest Checkout"])
cfg    = get_settings()


@router.post("/request-verification", response_model=RequestVerificationOut, status_code=201)
def request_verification(payload: RequestVerificationIn, request: Request, db: Session = Depends(get_db)):
    """
    Step 1 — Guest submits identity.
    Sends OTP to email AND WhatsApp simultaneously.
    Safe to call again (browser refresh) — reuses existing open session.
    """
    session = get_or_create_session(
        db,
        email=str(payload.email), phone=payload.phone,
        guest_name=payload.guest_name,
        ip_address=request.client.host if request.client else None,
    )
    e_otp = send_otp(db, session=session, channel=OtpChannel.email, purpose=OtpPurpose.checkout)
    w_otp = send_otp(db, session=session, channel=OtpChannel.sms,   purpose=OtpPurpose.checkout)

    return RequestVerificationOut(
        session_id=session.id,
        email_otp=OtpChannelInfo(
            otp_id=e_otp.id, channel="email",
            sent_to=mask_email(session.email), expires_in_secs=expire_secs(),
            dev_code=e_otp.plain_code if cfg.dev_show_code else None,
        ),
        sms_otp=OtpChannelInfo(
            otp_id=w_otp.id, channel="sms",
            sent_to=mask_phone(session.phone), expires_in_secs=expire_secs(),
            dev_code=w_otp.plain_code if cfg.dev_show_code else None,
        ),
        message="[DEV] Codes shown above." if cfg.dev_show_code else "OTPs sent to email and SMS.",
    )


@router.post("/verify", response_model=VerifyOtpOut)
def verify(payload: VerifyOtpIn, db: Session = Depends(get_db)):
    """
    Step 2 — Verify one channel. Call twice (email, then WhatsApp).
    session_token is returned only when BOTH channels are verified.
    """
    channel = OtpChannel(payload.channel)
    session = verify_otp(db, session_id=payload.session_id, otp_id=payload.otp_id, channel=channel, code=payload.code)
    both = session.email_verified and session.sms_verified

    return VerifyOtpOut(
        session_id=session.id, channel=payload.channel,
        email_verified=session.email_verified,
        sms_verified=session.sms_verified,
        session_token=session.session_token if both else None,
        session_expires_at=session.session_expires_at if both else None,
        message="Both verified — proceed to order." if both
                else f"{payload.channel.capitalize()} verified. Please also verify "
                     f"{'SMS' if channel == OtpChannel.email else 'email'}.",
    )


@router.post("/resend-otp", response_model=ResendOtpOut)
def resend_otp(payload: ResendOtpIn, db: Session = Depends(get_db)):
    """Resend OTP for one channel. Enforces cooldown and max-resend cap."""
    session = db.query(GuestCheckoutSession).filter_by(id=payload.session_id).first()
    if not session:
        raise HTTPException(404, "Checkout session not found.")

    otp = send_otp(db, session=session, channel=OtpChannel(payload.channel),
                   purpose=OtpPurpose.checkout, is_resend=True)
    left = cfg.otp_max_resends - otp.resend_count

    return ResendOtpOut(
        otp_id=otp.id, channel=payload.channel,
        expires_in_secs=expire_secs(), resends_left=left,
        dev_code=otp.plain_code if cfg.dev_show_code else None,
        message=f"New {payload.channel} OTP sent. {left} resend(s) remaining.",
    )
