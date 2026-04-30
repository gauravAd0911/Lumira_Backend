from sqlalchemy.orm import Session

from app.models.ledger import StockLedger


class LedgerRepository:
    """
    Handles stock audit logging.
    """

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        product_id: int,
        warehouse_id: int,
        change_type: str,
        quantity: int,
        reference_id: int | None = None,
        reference_type: str | None = None,
    ) -> None:
        entry = StockLedger(
            product_id=product_id,
            warehouse_id=warehouse_id,
            change_type=change_type,
            quantity=quantity,
            reference_id=reference_id,
            reference_type=reference_type,
        )

        self.db.add(entry)
        self.db.commit()