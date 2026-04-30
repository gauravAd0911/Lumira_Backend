from sqlalchemy.orm import Session
from app.models.tracking import Tracking


class TrackingRepository:

    def __init__(self, db: Session):
        self.db = db

    def add_tracking(self, order_id, status, message):
        track = Tracking(
            order_id=order_id,
            status=status,
            message=message
        )
        self.db.add(track)
        self.db.flush()

    def get_tracking(self, order_id):
        return self.db.query(Tracking).filter(Tracking.order_id == order_id).all()
