from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OrderItem(BaseModel):
    """
    Represents a snapshot of an order item.
    """

    product_id: str = Field(..., alias="productId")
    product_name: str = Field(..., alias="productName")
    price: float
    quantity: int
    image_url: Optional[str] = Field(None, alias="imageUrl")

    class Config:
        populate_by_name = True


class FinalizeOrderRequest(BaseModel):
    """
    Request payload to finalize an order.
    """

    total: float = Field(..., gt=0)
    payment_method: str = Field(..., alias="paymentMethod")
    shipping_address: str = Field(..., alias="shippingAddress")
    item_count: int = Field(..., gt=0, alias="itemCount")
    primary_label: str = Field(..., alias="primaryLabel")
    items: List[OrderItem]

    class Config:
        populate_by_name = True


class OrderResponse(BaseModel):
    """
    Response after order creation.
    """

    order_number: str = Field(..., alias="orderNumber")
    status: str

    class Config:
        populate_by_name = True


class OrderListItem(BaseModel):
    """
    Order summary for listing (mobile-friendly).
    """

    order_number: str = Field(..., alias="orderNumber")
    placed_on: datetime = Field(..., alias="placedOn")
    status: str
    status_label: str = Field(..., alias="statusLabel")
    total: float
    item_count: int = Field(..., alias="itemCount")
    primary_label: str = Field(..., alias="primaryLabel")
    shipping_address: str = Field(..., alias="shippingAddress")
    payment_method: str = Field(..., alias="paymentMethod")

    class Config:
        populate_by_name = True


class OrderDetailResponse(BaseModel):
    """
    Detailed order view.
    """

    order_number: str = Field(..., alias="orderNumber")
    placed_on: datetime = Field(..., alias="placedOn")
    status: str
    status_label: str = Field(..., alias="statusLabel")
    total: float
    item_count: int = Field(..., alias="itemCount")
    primary_label: str = Field(..., alias="primaryLabel")
    shipping_address: str = Field(..., alias="shippingAddress")
    payment_method: str = Field(..., alias="paymentMethod")
    items: List[OrderItem]

    class Config:
        populate_by_name = True
