from pydantic import BaseModel, Field


class StockValidationRequest(BaseModel):
    """
    Request schema for stock validation.
    """
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class StockValidationResponse(BaseModel):
    """
    Response schema for stock validation.
    """
    is_available: bool
    available_quantity: int = Field(..., ge=0)