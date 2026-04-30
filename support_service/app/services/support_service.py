# services/support_service.py

from sqlalchemy.orm import Session
from app.repository.support_repo import SupportRepository


class SupportService:

    @staticmethod
    def create_support_ticket(db: Session, payload: dict, user_id: int = None):
        data = payload.copy()
        data["user_id"] = user_id

        ticket = SupportRepository.create_ticket(db, data)

        # Future: trigger event/notification
        # publish_event("support.ticket.created", ticket.id)

        return ticket