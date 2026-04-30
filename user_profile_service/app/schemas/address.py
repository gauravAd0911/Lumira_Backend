from pydantic import BaseModel, Field
from typing import Optional


class AddressCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=10, max_length=15)
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: Optional[str] = "India"
    is_default: bool = False


class AddressResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: Optional[str] = "India"
    is_default: bool

    class Config:
        from_attributes = True