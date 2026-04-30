# api/support_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.support_schema import SupportCreate
from app.services.support_service import SupportService

router = APIRouter(prefix="/api/v1", tags=["Support"])


@router.post("/support/queries")
def create_support(payload: SupportCreate, db: Session = Depends(get_db)):
    ticket = SupportService.create_support_ticket(db, payload.dict())
    return {"id": ticket.id, "status": ticket.status}


@router.get("/support/options")
def get_support_options():
    return [
        {"type": "email", "value": "support@company.com"},
        {"type": "phone", "value": "+91 9999999999"},
    ]