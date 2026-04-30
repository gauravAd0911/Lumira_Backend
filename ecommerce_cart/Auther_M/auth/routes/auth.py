from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth.models.user import User
from auth.schemas.user_schema import APIResponse, OTPVerifyRequest, TokenResponse, UserCreate, UserLogin
from auth.services.auth_service import authenticate_user, create_or_update_pending_user, verify_user_otp
from auth.services.twilio_service import send_otp_sms
from auth.utils.jwt import create_access_token, create_refresh_token, verify_token

router = APIRouter()


@router.post("/register", response_model=APIResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a user, issue an OTP, and send it via Twilio."""

    try:
        user, otp_code, otp_expiry_minutes, _ = create_or_update_pending_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sms_status = send_otp_sms(user.mobile, otp_code, expiry_minutes=otp_expiry_minutes)
    if sms_status.get("status") != "sent":
        raise HTTPException(status_code=500, detail=sms_status.get("error") or "Failed to send OTP")

    return APIResponse(
        success=True,
        message="Registration successful. Verify the OTP sent to your mobile number.",
        data={
            "email": user.email,
            "mobile": user.mobile,
            "sms_status": sms_status,
        },
    )


@router.post("/verify-otp", response_model=APIResponse)
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP for a given email."""

    user = verify_user_otp(db, payload.email, payload.otp)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return APIResponse(
        success=True,
        message="OTP verified successfully. You can now log in.",
        data={"email": user.email, "is_verified": user.is_verified},
    )


@router.post("/login", response_model=APIResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login only after OTP verification."""

    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your OTP before logging in")

    access_token = create_access_token({"user_id": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"user_id": user.id, "role": user.role.value})

    return APIResponse(
        success=True,
        message="Login successful",
        data={
            "tokens": TokenResponse(access_token=access_token, refresh_token=refresh_token),
            "user": {
                "full_name": user.full_name,
                "email": user.email,
                "mobile": user.mobile,
                "role": user.role.value,
            },
        },
    )


@router.post("/refresh", response_model=APIResponse)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token."""

    payload = verify_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == payload["user_id"]).first()

    access_token = create_access_token({"user_id": user.id, "role": user.role.value})

    return APIResponse(success=True, message="Token refreshed", data={"access_token": access_token})


@router.post("/forgot-password", response_model=APIResponse)
def forgot_password(email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Generate a short-lived reset token without exposing it in logs."""

    user = db.query(User).filter(User.email == email).first()

    if user:
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=5)
        db.commit()

    return APIResponse(success=True, message="If the account exists, a reset token has been generated.")


@router.post("/reset-password", response_model=APIResponse)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
):
    """Reset password using a valid reset token."""

    from auth.utils.password import hash_password

    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.utcnow(),
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return APIResponse(success=True, message="Password reset successful")
