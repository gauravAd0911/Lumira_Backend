# app/schemas/tracking_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import List


class TrackingEvent(BaseModel):
    """Single tracking timeline event."""

    status: str
    label: str
    message: str
    timestamp: datetime


class TrackingResponse(BaseModel):
    """Tracking timeline response."""

    orderNumber: str
    timeline: List[TrackingEvent]