from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, String
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func

from database import Base


class Role(str, enum.Enum):
    """Role values stored on the user record."""

    ADMIN = "admin"
    USER = "user"
    VENDOR = "vendor"


class User(Base):
    """User table.

    Stores authentication fields plus OTP verification state.
    """

    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(20), index=True, nullable=True)

    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role), default=Role.USER, nullable=False)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    otp_code = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_verified_at = Column(DateTime, nullable=True)

    reset_token = Column(String(500), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
