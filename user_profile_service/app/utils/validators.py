import re
from fastapi import HTTPException
from app.core.constants import MAX_ADDRESS_LIMIT


# =========================
# REGEX PATTERNS
# =========================
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_REGEX = r"^[6-9]\d{9}$"  # Indian phone numbers
PINCODE_REGEX = r"^\d{6}$"


# =========================
# GENERIC VALIDATORS
# =========================
def validate_email(email: str) -> None:
    """Validate email format."""
    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(status_code=400, detail="Invalid email format")


def validate_phone(phone: str) -> None:
    """Validate Indian phone number."""
    if not re.match(PHONE_REGEX, phone):
        raise HTTPException(status_code=400, detail="Invalid phone number")


def validate_pincode(pincode: str) -> None:
    """Validate Indian postal code (6 digits)."""
    if not re.match(PINCODE_REGEX, pincode):
        raise HTTPException(status_code=400, detail="Invalid postal code")


def validate_required_string(value: str, field_name: str) -> None:
    """Check if string is not empty."""
    if not value or not value.strip():
        raise HTTPException(status_code=400, detail=f"{field_name} is required")


# =========================
# ADDRESS VALIDATORS
# =========================
def validate_address_payload(data: dict) -> None:
    """
    Validate full address payload.
    Used before creating/updating address.
    """
    validate_required_string(data.get("full_name"), "Full name")
    validate_phone(data.get("phone"))
    validate_required_string(data.get("address_line1"), "Address Line 1")
    validate_required_string(data.get("city"), "City")
    validate_required_string(data.get("state"), "State")
    validate_pincode(data.get("postal_code"))


def validate_address_limit(count: int) -> None:
    """Check max address limit."""
    if count >= MAX_ADDRESS_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Address limit exceeded (max {MAX_ADDRESS_LIMIT})"
        )


# =========================
# BUSINESS VALIDATORS
# =========================
def validate_address_ownership(address, user_id: str) -> None:
    """Ensure address belongs to user."""
    if not address or address.user_id != user_id:
        raise HTTPException(status_code=404, detail="Address not found")


def validate_default_address_exists(address) -> None:
    """Check if address exists before setting default."""
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")