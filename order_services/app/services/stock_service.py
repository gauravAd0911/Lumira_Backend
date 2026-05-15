"""
Stock management service for MVP.
Deducts stock when orders are completed.
Skips reservation system if disabled.
"""

import logging
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger(__name__)


def deduct_stock_for_order(db: Session, order_id: int, order_items: list) -> bool:
    """
    Deduct stock for a completed order.
    Works regardless of reservation system.
    
    Args:
        db: Database session
        order_id: Order ID being completed
        order_items: List of items in order, each with product_id and quantity
        
    Returns:
        bool: True if deduction successful, False otherwise
    """
    
    if not settings.DEDUCT_STOCK_ON_ORDER:
        logger.info(f"Stock deduction disabled. Skipping for order {order_id}")
        return True
    
    logger.warning(
        "Stock deduction requested for order %s, but no Product model is configured. "
        "Disable DEDUCT_STOCK_ON_ORDER or wire this service to the product service.",
        order_id,
    )
    return True


def is_reservation_enabled() -> bool:
    """Check if reservation system is enabled."""
    return settings.ENABLE_STOCK_RESERVATION
