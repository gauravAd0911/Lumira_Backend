from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth.middleware.auth_guard import get_current_user
from auth.models.user import OtpPurpose, User
from auth.schemas.user_schema import (
    APIResponse,
    AuthResponse,
    ForgotInitiateRequest,
    ForgotInitiateResponse,
    ForgotVerifyRequest,
    ForgotVerifyResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    SignupInitiateRequest,
    SignupInitiateResponse,
    SignupVerifyRequest,
    UserOut,
)
from auth.services.auth_service import authenticate_by_identifier, create_pending_user, mark_user_verified
from auth.services.identifier_service import normalize_identifier
from auth.services.otp_context_service import create_or_refresh_context, verify_context_otp
from auth.services.password_reset_service import consume_reset_token, create_reset_token
from auth.services.session_service import create_session, refresh_session, revoke_session
from auth.services.twilio_service import send_otp_sms

router = APIRouter()

OTP_SENT_MESSAGE = "OTP sent successfully."


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
    )


@router.post(
    "/signup/initiate",
    response_model=SignupInitiateResponse,
    responses={
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)
def signup_initiate(payload: SignupInitiateRequest, db: Annotated[Session, Depends(get_db)]):
    """Signup initiate.

    Creates/updates a pending user, creates an OTP context, and sends OTP via SMS.
    """

    try:
        user = create_pending_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = create_or_refresh_context(
        db,
        purpose=OtpPurpose.SIGNUP,
        user=user,
        email=user.email,
        phone=user.phone,
    )

    sms = send_otp_sms(user.phone or "", result.otp, expiry_minutes=int(result.otp_expiry_seconds / 60))
    if sms.get("status") != "sent":
        raise HTTPException(status_code=500, detail=sms.get("error") or "Failed to send OTP")

    return SignupInitiateResponse(
        context_id=result.context_id,
        message=OTP_SENT_MESSAGE,
        otp_expiry_seconds=result.otp_expiry_seconds,
    )


@router.post(
    "/signup/verify-otp",
    response_model=AuthResponse,
    responses={
        400: {"description": "Bad request"},
        429: {"description": "Too many attempts"},
    },
)
def signup_verify(payload: SignupVerifyRequest, db: Annotated[Session, Depends(get_db)]):
    """Signup verify.

    Verifies OTP for the context and returns an authenticated token pair.
    """

    try:
        context = verify_context_otp(db, payload.context_id, payload.otp)
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if context.purpose != OtpPurpose.SIGNUP:
        raise HTTPException(status_code=400, detail="Invalid context")

    user = db.query(User).filter(User.id == context.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    mark_user_verified(db, user)
    access, refresh = create_session(db, user)

    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_out(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    """Login.

    Accepts email or phone as identifier.
    """

    user = authenticate_by_identifier(db, payload.identifier, payload.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="OTP verification required")

    access, refresh = create_session(db, user)
    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_out(user))


@router.post(
    "/password/forgot/initiate",
    response_model=ForgotInitiateResponse,
    responses={
        500: {"description": "Internal server error"},
    },
)
def forgot_initiate(payload: ForgotInitiateRequest, db: Annotated[Session, Depends(get_db)]):
    """Forgot password initiate.

    Sends OTP to the user's phone if user exists, but never leaks user existence.
    """

    kind, ident = normalize_identifier(payload.identifier)

    query = db.query(User)
    user = query.filter(User.email == ident).first() if kind == "email" else query.filter(User.phone == ident).first()

    if not user:
        return ForgotInitiateResponse(context_id="", message=OTP_SENT_MESSAGE, otp_expiry_seconds=300)

    result = create_or_refresh_context(
        db,
        purpose=OtpPurpose.PASSWORD_FORGOT,
        user=user,
        email=user.email,
        phone=user.phone,
    )

    sms = send_otp_sms(user.phone or "", result.otp, expiry_minutes=int(result.otp_expiry_seconds / 60))
    if sms.get("status") != "sent":
        raise HTTPException(status_code=500, detail=sms.get("error") or "Failed to send OTP")

    return ForgotInitiateResponse(
        context_id=result.context_id,
        message=OTP_SENT_MESSAGE,
        otp_expiry_seconds=result.otp_expiry_seconds,
    )


@router.post(
    "/password/forgot/verify-otp",
    response_model=ForgotVerifyResponse,
    responses={
        400: {"description": "Bad request"},
        429: {"description": "Too many attempts"},
    },
)
def forgot_verify(payload: ForgotVerifyRequest, db: Annotated[Session, Depends(get_db)]):
    """Forgot password verify OTP.

    Verifies OTP for the context and returns a reset token.
    """

    try:
        context = verify_context_otp(db, payload.context_id, payload.otp)
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if context.purpose != OtpPurpose.PASSWORD_FORGOT:
        raise HTTPException(status_code=400, detail="Invalid context")

    user = db.query(User).filter(User.id == context.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    reset_token, expiry_seconds = create_reset_token(db, user)
    return ForgotVerifyResponse(reset_token=reset_token, reset_token_expiry_seconds=expiry_seconds)


@router.post(
    "/password/reset",
    response_model=APIResponse,
    responses={
        400: {"description": "Bad request"},
    },
)
def password_reset(payload: PasswordResetRequest, db: Annotated[Session, Depends(get_db)]):
    """Password reset.

    Consumes a reset token and updates the password.
    """

    from auth.utils.password import hash_password

    user = consume_reset_token(db, payload.reset_token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return APIResponse(success=True, message="Password reset successful")


@router.post(
    "/token/refresh",
    response_model=AuthResponse,
    responses={
        401: {"description": "Unauthorized"},
    },
)
def token_refresh(payload: RefreshTokenRequest, db: Annotated[Session, Depends(get_db)]):
    """Refresh token rotation."""

    try:
        access, refresh, user = refresh_session(db, payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_out(user))


@router.post(
    "/logout",
    response_model=APIResponse,
)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]):
    """Logout (session revocation)."""

    revoke_session(db, payload.refresh_token)
    return APIResponse(success=True, message="Logged out")


@router.get(
    "/me",
    response_model=UserOut,
    responses={
        401: {"description": "Unauthorized"},
    },
)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return current user session (fast app boot dependency)."""

    return _user_out(current_user)
