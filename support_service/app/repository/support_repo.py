# repository/support_repo.py

from sqlalchemy.orm import Session
from app.utils.constants import TicketStatus
from app.models.support_model import SupportTicket


class SupportRepository:

    @staticmethod
    def create_ticket(db: Session, data: dict) -> SupportTicket:
        ticket = SupportTicket(**data, status=TicketStatus.OPEN)
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_user_tickets(db: Session, user_id: int):
        return db.query(SupportTicket).filter(
            SupportTicket.user_id == user_id
        ).all()