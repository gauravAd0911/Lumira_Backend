from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SignupInitiateRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(min_length=8, max_length=25)
    password: str = Field(min_length=6, max_length=255)


class SignupInitiateResponse(BaseModel):
    context_id: str = Field(alias="context_id")
    message: str
    otp_expiry_seconds: int


class SignupVerifyRequest(BaseModel):
    context_id: str = Field(alias="contextId")
    otp: str = Field(min_length=4, max_length=10)


class LoginRequest(BaseModel):
    identifier: str
    password: str


class ForgotInitiateRequest(BaseModel):
    identifier: str


class ForgotInitiateResponse(BaseModel):
    context_id: str
    message: str
    otp_expiry_seconds: int


class ForgotVerifyRequest(BaseModel):
    context_id: str = Field(alias="contextId")
    otp: str = Field(min_length=4, max_length=10)


class ForgotVerifyResponse(BaseModel):
    reset_token: str
    reset_token_expiry_seconds: int


class PasswordResetRequest(BaseModel):
    reset_token: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    role: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
