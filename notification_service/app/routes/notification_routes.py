from typing import Annotated, Generator, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification_model import Device
from app.schemas.notification_schema import (
    DeviceRegister,
    NotificationCreate,
    NotificationResponse,
)
from app.services.notification_service import NotificationService


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)


# -------------------------------
# Dependency
# -------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for each request.
    Ensures proper cleanup after request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]


# -------------------------------
# Device APIs
# -------------------------------
@router.post("/devices/register", status_code=status.HTTP_201_CREATED)
def register_device(payload: DeviceRegister, db: DBSession) -> dict:
    """
    Register a user device for notifications.
    """
    device = Device(
        user_id=payload.user_id,
        device_token=payload.device_token,
        platform=payload.platform,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "message": "Device registered successfully",
        "device_id": device.id,
    }


@router.delete("/devices/{device_id}", status_code=status.HTTP_200_OK)
def delete_device(device_id: int, db: DBSession) -> dict:
    """
    Remove a registered device.
    """
    device = db.get(Device, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    db.delete(device)
    db.commit()

    return {"message": f"Device {device_id} removed successfully"}


# -------------------------------
# Notification APIs
# -------------------------------
@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: DBSession) -> NotificationResponse:
    """
    Create a notification for a user.
    """
    return NotificationService.create_notification(
        db=db,
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        type_=payload.type,
    )


@router.get("", response_model=List[NotificationResponse])
def get_notifications(user_id: int, db: DBSession) -> List[NotificationResponse]:
    """
    Fetch all notifications for a given user.
    """
    notifications = NotificationService.get_notifications(db, user_id)
    return notifications if notifications else []


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: DBSession) -> NotificationResponse:
    """
    Mark a notification as read.
    """
    notification = NotificationService.mark_as_read(db, notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification
