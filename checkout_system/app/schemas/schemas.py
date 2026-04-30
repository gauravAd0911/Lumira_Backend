from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Shared ─────────────────────────────────────────────────────
class AddressIn(BaseModel):
    full_name:   str = Field(..., min_length=2, max_length=200)
    line1:       str = Field(..., min_length=3, max_length=255)
    line2:       Optional[str] = None
    city:        str = Field(..., min_length=1, max_length=100)
    state:       Optional[str] = None
    postal_code: str = Field(..., min_length=3, max_length=20)
    country:     str = Field("US", min_length=2, max_length=2)
    phone:       Optional[str] = None


class AddressOut(AddressIn):
    id:         str
    created_at: datetime
    class Config: from_attributes = True


class OrderItemIn(BaseModel):
    product_id: str
    sku:        Optional[str] = None
    name:       str
    quantity:   int     = Field(..., ge=1, le=100)
    unit_price: Decimal = Field(..., ge=0)


# ── Guest Checkout — Request OTPs ──────────────────────────────
class RequestVerificationIn(BaseModel):
    guest_name: Optional[str] = Field(None, max_length=200)
    email:      EmailStr
    phone:      str = Field(..., min_length=7, max_length=30,
                            description="E.164 format, e.g. +919876543210")


class OtpChannelInfo(BaseModel):
    otp_id:          str
    channel:         str
    sent_to:         str           # masked address
    expires_in_secs: int
    dev_code:        Optional[str] = None


class RequestVerificationOut(BaseModel):
    session_id: str
    email_otp:  OtpChannelInfo
    sms_otp:    OtpChannelInfo
    message:    str


# ── Guest Checkout — Verify one channel ───────────────────────
class VerifyOtpIn(BaseModel):
    session_id: str
    otp_id:     str
    channel:    str = Field(..., pattern="^(email|sms)$")
    code:       str = Field(..., min_length=4, max_length=10)


class VerifyOtpOut(BaseModel):
    session_id:       str
    channel:          str
    email_verified:   bool
    sms_verified: bool
    session_token:    Optional[str]      = None   # issued only when both verified
    session_expires_at: Optional[datetime] = None
    message:          str


# ── Resend OTP ─────────────────────────────────────────────────
class ResendOtpIn(BaseModel):
    session_id: str
    channel:    str = Field(..., pattern="^(email|sms)$")


class ResendOtpOut(BaseModel):
    otp_id:          str
    channel:         str
    expires_in_secs: int
    resends_left:    int
    dev_code:        Optional[str] = None
    message:         str


# ── Place Guest Order ──────────────────────────────────────────
class GuestOrderIn(BaseModel):
    session_token:    str
    items:            List[OrderItemIn] = Field(..., min_length=1)
    shipping_address: AddressIn
    billing_address:  Optional[AddressIn] = None
    payment_method:   str = Field("cod", max_length=50)
    notes:            Optional[str] = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v):
        if not v:
            raise ValueError("Order must have at least one item.")
        return v


class GuestOrderOut(BaseModel):
    id:                str
    order_number:      str
    guest_name:        str
    guest_email:       str
    guest_phone:       Optional[str]
    email_verified:    bool
    sms_verified: bool
    items:             List[Dict[str, Any]]
    subtotal:          Decimal
    shipping_amount:   Decimal
    tax_amount:        Decimal
    discount_amount:   Decimal
    total_amount:      Decimal
    currency:          str
    status:            str
    payment_status:    str
    shipping_address:  Optional[AddressOut] = None
    created_at:        datetime
    class Config: from_attributes = True


# ── Order Lookup ───────────────────────────────────────────────
class LookupRequestIn(BaseModel):
    email:        EmailStr
    order_number: Optional[str] = None


class LookupRequestOut(BaseModel):
    session_id:      str
    otp_id:          str
    expires_in_secs: int
    dev_code:        Optional[str] = None
    message:         str


class LookupVerifyIn(BaseModel):
    session_id:   str
    otp_id:       str
    code:         str = Field(..., min_length=4, max_length=10)
    order_number: Optional[str] = None


class LookupVerifyOut(BaseModel):
    orders:  List[GuestOrderOut]
    message: str


# ── Products ───────────────────────────────────────────────────
class ProductOut(BaseModel):
    id:            str
    name:          str
    slug:          str
    description:   Optional[str]
    price:         Decimal
    compare_price: Optional[Decimal]
    sku:           Optional[str]
    stock_qty:     int
    images:        List[Any]
    category:      Optional[str] = None
    class Config: from_attributes = True


class CheckoutItemIn(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=100)


class CheckoutValidateIn(BaseModel):
    items: List[CheckoutItemIn] = Field(..., min_length=1)
    address_id: Optional[str] = None
    guest_token: Optional[str] = None


class CheckoutIssueOut(BaseModel):
    code: str
    message: str
    product_id: Optional[str] = None


class CheckoutPricingOut(BaseModel):
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    shipping: Decimal = Decimal("0")
    total: Decimal
    currency: str = "INR"


class CheckoutValidateOut(BaseModel):
    cart_valid: bool
    delivery_valid: bool
    inventory_valid: bool
    pricing: CheckoutPricingOut
    issues: List[CheckoutIssueOut]


class CheckoutSessionIn(CheckoutValidateIn):
    pass


class CheckoutSessionOut(BaseModel):
    checkout_session_id: str
    reservation_required: bool = True
    payable_amount: Decimal
    currency: str = "INR"
    expires_at: datetime
