from pydantic import BaseModel, ConfigDict

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
