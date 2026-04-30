"""
otp_service.py — Dual-channel OTP engine (Email + SMS)

Responsibilities:
  - Session lifecycle (create / reuse)
  - Code generation, hashing, dispatch
  - Attempt throttling, resend cooldown, lockout
  - Dual-verification gate → issues session_token
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import GuestCheckoutSession, GuestOtp, OtpChannel, OtpPurpose, OtpStatus

cfg = get_settings()


# ── Utilities ──────────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def _hash(code: str) -> str:
    return sha256(code.strip().encode()).hexdigest()

def _expires_at() -> datetime:
    return _now() + timedelta(minutes=cfg.otp_expire_minutes)

def _expire_secs() -> int:
    return cfg.otp_expire_minutes * 60

def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"

def _mask_phone(phone: str) -> str:
    return phone[:3] + "***" + phone[-3:] if len(phone) > 6 else "***"


# ── OTP Delivery ───────────────────────────────────────────────
import logging
_log = logging.getLogger(__name__)

def _deliver(channel: OtpChannel, destination: str, code: str, purpose: str) -> None:
    """Dispatch OTP to the right channel."""
    if channel == OtpChannel.sms:
        if not cfg.sms_enabled:
            _log.warning("SMS_ENABLED=false — skipping SMS to %s. Code: %s", destination, code)
            return
        if not cfg.twilio_account_sid or cfg.twilio_account_sid.startswith("AC" + "x"):
            _log.error("Twilio credentials not configured in .env — SMS not sent.")
            return
        try:
            from twilio.rest import Client
            msg = Client(cfg.twilio_account_sid, cfg.twilio_auth_token).messages.create(
                body=f"Your ShopFlow OTP: {code}\nExpires in {cfg.otp_expire_minutes} min. Do not share.",
                from_=cfg.twilio_sms_from,
                to=destination,
            )
            _log.info("SMS sent to %s — SID: %s", destination, msg.sid)
        except Exception as e:
            _log.error("Twilio SMS failed to %s: %s", destination, e)
    elif channel == OtpChannel.email:
        # Plug SMTP / SendGrid here
        _log.info("Email OTP for %s — code visible in dev_code field", destination)


# ── Session ────────────────────────────────────────────────────
def get_or_create_session(
    db: Session, *, email: str, phone: str,
    guest_name: str | None = None,
    purpose: str = "checkout",
    ip_address: str | None = None,
) -> GuestCheckoutSession:
    """
    Reuse an open (un-tokenised) session for the same email+phone.
    Creates a new one if email/phone changed (guest edited mid-flow).
    """
    email = email.lower().strip()
    existing = (
        db.query(GuestCheckoutSession)
        .filter_by(email=email, phone=phone, purpose=purpose)
        .filter(GuestCheckoutSession.session_token.is_(None))
        .order_by(GuestCheckoutSession.created_at.desc())
        .first()
    )
    if existing:
        if guest_name:
            existing.guest_name = guest_name
        existing.updated_at = _now()
        db.commit()
        return existing

    session = GuestCheckoutSession(
        email=email, phone=phone, purpose=purpose,
        guest_name=guest_name, ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_lookup_session(
    db: Session, *, email: str, ip_address: str | None = None,
) -> GuestCheckoutSession:
    """Lookup needs email OTP only — SMS gate pre-verified."""
    session = GuestCheckoutSession(
        email=email.lower().strip(), phone="lookup",
        purpose="order_lookup",
        sms_verified=True,   # skip SMS gate for read-only lookup
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ── Send OTP ───────────────────────────────────────────────────
def send_otp(
    db: Session, *, session: GuestCheckoutSession,
    channel: OtpChannel, purpose: OtpPurpose, is_resend: bool = False,
) -> GuestOtp:
    if is_resend:
        latest = _latest_otp(db, session.id, channel, purpose)
        if latest:
            if latest.resend_count >= cfg.otp_max_resends:
                raise HTTPException(429, f"Max resends reached for {channel.value}. Start a new session.")
            if latest.last_resent_at:
                wait = int(((_now() - latest.last_resent_at).total_seconds()))
                if wait < cfg.otp_resend_cooldown_secs:
                    raise HTTPException(429, f"Wait {cfg.otp_resend_cooldown_secs - wait}s before resending.")
            latest.status = OtpStatus.expired  # invalidate previous code
            latest.resend_count += 1
            latest.last_resent_at = _now()
            new_resend_count = latest.resend_count
        else:
            new_resend_count = 0
    else:
        new_resend_count = 0

    code = _gen_code()
    otp = GuestOtp(
        session_id=session.id, channel=channel, purpose=purpose,
        code_hash=_hash(code), expires_at=_expires_at(),
        resend_count=new_resend_count,
        last_resent_at=_now() if is_resend else None,
        plain_code=code if cfg.dev_show_code else None,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)

    destination = session.email if channel == OtpChannel.email else session.phone
    _deliver(channel, destination, code, purpose.value)
    return otp


def _latest_otp(db: Session, session_id: str, channel: OtpChannel, purpose: OtpPurpose) -> GuestOtp | None:
    return (
        db.query(GuestOtp)
        .filter_by(session_id=session_id, channel=channel, purpose=purpose)
        .order_by(GuestOtp.created_at.desc())
        .first()
    )


# ── Verify OTP ─────────────────────────────────────────────────
def verify_otp(
    db: Session, *, session_id: str, otp_id: str,
    channel: OtpChannel, code: str,
) -> GuestCheckoutSession:
    """
    Validates submitted code. Updates session verification flags.
    Issues session_token when both channels are verified.
    Returns the updated session.
    """
    otp = db.query(GuestOtp).filter_by(id=otp_id, session_id=session_id).first()
    if not otp:
        raise HTTPException(404, "OTP record not found.")

    if otp.status == OtpStatus.locked:
        raise HTTPException(429, "OTP locked after too many attempts.")
    if otp.status == OtpStatus.verified:
        raise HTTPException(400, "OTP already used.")
    if otp.status == OtpStatus.expired or _now() > otp.expires_at:
        otp.status = OtpStatus.expired
        db.commit()
        raise HTTPException(410, "OTP expired. Request a new code.")

    if _hash(code.strip()) != otp.code_hash:
        otp.attempts += 1
        if otp.attempts >= cfg.otp_max_attempts:
            otp.status = OtpStatus.locked
        db.commit()
        left = max(0, cfg.otp_max_attempts - otp.attempts)
        raise HTTPException(400, f"Invalid code. {left} attempt(s) left.")

    # Correct — mark verified
    otp.status = OtpStatus.verified
    otp.verified_at = _now()

    session = db.query(GuestCheckoutSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(404, "Checkout session not found.")

    if channel == OtpChannel.email:
        session.email_verified = True
    else:
        session.sms_verified = True

    # Issue master token only when both channels done
    if session.email_verified and session.sms_verified and not session.session_token:
        session.session_token = secrets.token_urlsafe(40)
        session.session_expires_at = _now() + timedelta(hours=24)

    session.updated_at = _now()
    db.commit()
    db.refresh(session)
    return session


# ── Session Guards ─────────────────────────────────────────────
def require_checkout_session(db: Session, token: str) -> GuestCheckoutSession:
    """Used by order placement — both channels must be verified."""
    s = db.query(GuestCheckoutSession).filter_by(session_token=token).first()
    if not s:
        raise HTTPException(401, "Invalid session token.")
    if not (s.email_verified and s.sms_verified):
        raise HTTPException(403, "Both email and SMS must be verified.")
    if s.session_expires_at and _now() > s.session_expires_at:
        raise HTTPException(401, "Session expired. Please restart checkout.")
    return s


def require_lookup_session(db: Session, token: str) -> GuestCheckoutSession:
    """Used by order lookup — email verification sufficient."""
    s = db.query(GuestCheckoutSession).filter_by(session_token=token, purpose="order_lookup").first()
    if not s or not s.email_verified:
        raise HTTPException(401, "Invalid or unverified lookup session.")
    if s.session_expires_at and _now() > s.session_expires_at:
        raise HTTPException(401, "Lookup session expired.")
    return s


# ── Exported helpers ───────────────────────────────────────────
expire_secs = _expire_secs
mask_email  = _mask_email
mask_phone  = _mask_phone
