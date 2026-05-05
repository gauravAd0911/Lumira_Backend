from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None


class DeviceRegister(BaseModel):
    user_id: int
    device_token: str
    platform: str

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: str

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    is_read: bool
