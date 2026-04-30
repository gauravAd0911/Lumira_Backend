from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VENDOR = "vendor"


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    password: str
    role: Role = Role.USER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
