# schemas/support_schema.py

from pydantic import BaseModel, EmailStr
from typing import Optional


class SupportCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    message: str


class SupportResponse(BaseModel):
    id: int
    status: str