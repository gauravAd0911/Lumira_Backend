from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.stock_repo import StockRepository
from app.schemas.inventory import StockValidationRequest, StockValidationResponse


class InventoryService:
    """
    Handles stock validation logic.
    """

    def __init__(self, db: Session):
        self.stock_repo = StockRepository(db)

    def validate_stock(self, request: StockValidationRequest) -> StockValidationResponse:
        """
        Validate if sufficient stock is available.

        :param request: Stock validation request
        :return: Stock validation response
        """
        stock = self.stock_repo.get_stock_for_update(
            product_id=request.product_id,
            warehouse_id=request.warehouse_id
        )

        if not stock:
            return StockValidationResponse(
                is_available=False,
                available_quantity=0
            )

        is_available = stock.available_quantity >= request.quantity

        return StockValidationResponse(
            is_available=is_available,
            available_quantity=stock.available_quantity
        )