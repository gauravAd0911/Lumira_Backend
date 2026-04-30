# app/core/constants.py

class OrderStatus:
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


STATUS_LABELS = {
    OrderStatus.PLACED: "Order Placed",
    OrderStatus.CONFIRMED: "Confirmed",
    OrderStatus.PACKED: "Packed",
    OrderStatus.SHIPPED: "Shipped",
    OrderStatus.OUT_FOR_DELIVERY: "Out for Delivery",
    OrderStatus.DELIVERED: "Delivered",
    OrderStatus.CANCELLED: "Cancelled",
    OrderStatus.PAYMENT_FAILED: "Payment Failed",
}